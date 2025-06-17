#include "core/shared_memory_manager.h"
#include "core/metrics_collector.h"
#include <App.h>
#include <thread>
#include <iostream>
#include <signal.h>
#include <atomic>
#include <chrono>
#include <sstream>

namespace hft {

class WebSocketServer {
public:
    WebSocketServer(int port = 8080) : port_(port), running_(true) {
        try {
            orderbook_shm_.open();
            metrics_shm_.open();
            trades_shm_.open();
        } catch (const std::exception& e) {
            std::cerr << "Failed to open shared memory: " << e.what() << std::endl;
            throw;
        }
    }
    
    void run() {
        std::cout << "Starting WebSocket server on port " << port_ << std::endl;
        
        auto app = uWS::App({
            .key_file_name = nullptr,
            .cert_file_name = nullptr,
            .passphrase = nullptr,
            .dh_params_file_name = nullptr,
            .ca_file_name = nullptr,
            .ssl_ciphers = nullptr
        });
        
        // WebSocket endpoint for order book updates
        app.ws<UserData>("/*", {
            .compression = uWS::SHARED_COMPRESSOR,
            .maxCompressedSize = 64 * 1024,
            .maxBackpressure = 64 * 1024,
            .closeOnBackpressureLimit = true,
            .resetIdleTimeoutOnSend = false,
            .sendPingsAutomatically = true,
            .maxLifetime = 0,
            
            .upgrade = nullptr,
            
            .open = [this](auto* ws) {
                std::cout << "Client connected" << std::endl;
                ws->subscribe("orderbook");
                ws->subscribe("metrics");
                ws->subscribe("trades");
            },
            
            .message = [this](auto* ws, std::string_view message, uWS::OpCode opCode) {
                // Handle client messages if needed
            },
            
            .close = [](auto* ws, int code, std::string_view message) {
                std::cout << "Client disconnected" << std::endl;
            }
        });
        
        // HTTP endpoint for health check
        app.get("/health", [](auto* res, auto* req) {
            res->writeHeader("Content-Type", "application/json");
            res->end("{\"status\":\"ok\",\"timestamp\":" + std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count()) + "}");
        });
        
        // Start broadcast threads
        std::thread orderbook_thread([this, &app]() {
            broadcast_orderbook_updates(app);
        });
        
        std::thread metrics_thread([this, &app]() {
            broadcast_metrics_updates(app);
        });
        
        std::thread trades_thread([this, &app]() {
            broadcast_trade_updates(app);
        });
        
        // Listen on port
        app.listen(port_, [this](auto* token) {
            if (token) {
                std::cout << "WebSocket server listening on port " << port_ << std::endl;
            } else {
                std::cerr << "Failed to listen on port " << port_ << std::endl;
                running_ = false;
            }
        });
        
        // Run until stopped
        while (running_) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        orderbook_thread.join();
        metrics_thread.join();
        trades_thread.join();
    }
    
    void stop() {
        running_ = false;
    }

private:
    struct UserData {
        // User-specific data if needed
    };
    
    int port_;
    std::atomic<bool> running_;
    
    SharedMemoryManager<SharedOrderBook> orderbook_shm_{"/hft_orderbook"};
    SharedMemoryManager<SharedMetrics> metrics_shm_{"/hft_metrics"};
    SharedMemoryManager<SharedTrades> trades_shm_{"/hft_trades"};
    
    uint64_t last_orderbook_seq_ = 0;
    uint64_t last_metrics_seq_ = 0;
    
    void broadcast_orderbook_updates(uWS::App& app) {
        while (running_) {
            auto* shared_ob = orderbook_shm_.get();
            if (shared_ob && shared_ob->ready.load()) {
                uint64_t current_seq = shared_ob->sequence_number.load();
                if (current_seq > last_orderbook_seq_) {
                    std::string json = serialize_orderbook(shared_ob->snapshot);
                    app.publish("orderbook", json, uWS::OpCode::TEXT);
                    last_orderbook_seq_ = current_seq;
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
    
    void broadcast_metrics_updates(uWS::App& app) {
        while (running_) {
            auto* shared_metrics = metrics_shm_.get();
            if (shared_metrics && shared_metrics->ready.load()) {
                uint64_t current_seq = shared_metrics->sequence_number.load();
                if (current_seq > last_metrics_seq_) {
                    std::string json = serialize_metrics(shared_metrics->metrics);
                    app.publish("metrics", json, uWS::OpCode::TEXT);
                    last_metrics_seq_ = current_seq;
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    
    void broadcast_trade_updates(uWS::App& app) {
        while (running_) {
            auto* shared_trades = trades_shm_.get();
            if (shared_trades) {
                Trade trade;
                while (shared_trades->pop(trade)) {
                    std::string json = serialize_trade(trade);
                    app.publish("trades", json, uWS::OpCode::TEXT);
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }
    
    std::string serialize_orderbook(const OrderBookSnapshot& snapshot) {
        std::ostringstream oss;
        oss << "{\"type\":\"orderbook\",\"symbol\":\"" << snapshot.symbol << "\",";
        oss << "\"timestamp\":" << snapshot.timestamp.count() << ",";
        oss << "\"bids\":[";
        
        for (uint32_t i = 0; i < snapshot.bid_count; ++i) {
            if (i > 0) oss << ",";
            oss << "[" << snapshot.bids[i].price / 100.0 << "," 
                << snapshot.bids[i].quantity << "," 
                << snapshot.bids[i].order_count << "]";
        }
        
        oss << "],\"asks\":[";
        for (uint32_t i = 0; i < snapshot.ask_count; ++i) {
            if (i > 0) oss << ",";
            oss << "[" << snapshot.asks[i].price / 100.0 << "," 
                << snapshot.asks[i].quantity << "," 
                << snapshot.asks[i].order_count << "]";
        }
        
        oss << "]}";
        return oss.str();
    }
    
    std::string serialize_metrics(const SystemMetrics& metrics) {
        std::ostringstream oss;
        oss << "{\"type\":\"metrics\",";
        oss << "\"timestamp\":" << metrics.timestamp.count() << ",";
        oss << "\"cpu_usage\":" << metrics.cpu_usage / 10.0 << ",";
        oss << "\"memory_usage\":" << metrics.memory_usage_bytes << ",";
        oss << "\"network_sent\":" << metrics.network_bytes_sent << ",";
        oss << "\"network_recv\":" << metrics.network_bytes_recv << ",";
        oss << "\"orders_processed\":" << metrics.orders_processed << ",";
        oss << "\"trades_executed\":" << metrics.trades_executed << ",";
        oss << "\"avg_latency_ns\":" << metrics.avg_latency_ns << ",";
        oss << "\"min_latency_ns\":" << metrics.min_latency_ns << ",";
        oss << "\"max_latency_ns\":" << metrics.max_latency_ns << "}";
        return oss.str();
    }
    
    std::string serialize_trade(const Trade& trade) {
        std::ostringstream oss;
        oss << "{\"type\":\"trade\",";
        oss << "\"symbol\":\"" << trade.symbol << "\",";
        oss << "\"price\":" << trade.price / 100.0 << ",";
        oss << "\"quantity\":" << trade.quantity << ",";
        oss << "\"timestamp\":" << trade.timestamp.count() << ",";
        oss << "\"buy_order_id\":" << trade.buy_order_id << ",";
        oss << "\"sell_order_id\":" << trade.sell_order_id << "}";
        return oss.str();
    }
};

} // namespace hft

static hft::WebSocketServer* g_server = nullptr;

void signal_handler(int signal) {
    if (g_server) {
        g_server->stop();
    }
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    int port = 8080;
    if (argc > 1) {
        port = std::atoi(argv[1]);
    }
    
    try {
        hft::WebSocketServer server(port);
        g_server = &server;
        server.run();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}