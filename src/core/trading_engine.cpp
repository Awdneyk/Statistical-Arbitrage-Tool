#include "core/order_book.h"
#include "core/shared_memory_manager.h"
#include "core/metrics_collector.h"
#include <iostream>
#include <thread>
#include <signal.h>
#include <random>

namespace hft {

class TradingEngine {
public:
    TradingEngine() 
        : orderbook_shm_("/hft_orderbook"),
          metrics_shm_("/hft_metrics"),
          trades_shm_("/hft_trades"),
          order_book_("BTCUSD"),
          running_(true) {
        
        // Set up shared memory
        try {
            orderbook_shm_.create();
            metrics_shm_.create();
            trades_shm_.create();
        } catch (const std::exception& e) {
            std::cerr << "Failed to create shared memory: " << e.what() << std::endl;
            throw;
        }
        
        // Set up trade callback
        order_book_.set_trade_callback([this](const Trade& trade) {
            handle_trade(trade);
        });
    }
    
    ~TradingEngine() {
        running_ = false;
        orderbook_shm_.unlink();
        metrics_shm_.unlink();
        trades_shm_.unlink();
    }
    
    void run() {
        std::cout << "Starting HFT Trading Engine..." << std::endl;
        
        // Start metrics update thread
        std::thread metrics_thread([this]() {
            while (running_) {
                update_metrics();
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        });
        
        // Start order book update thread
        std::thread orderbook_thread([this]() {
            while (running_) {
                auto snapshot = order_book_.get_snapshot();
                auto* shared_ob = orderbook_shm_.get();
                if (shared_ob) {
                    shared_ob->sequence_number.fetch_add(1);
                    shared_ob->snapshot = snapshot;
                    shared_ob->ready.store(true);
                }
                std::this_thread::sleep_for(std::chrono::microseconds(100));
            }
        });
        
        // Simulate order flow
        simulate_order_flow();
        
        metrics_thread.join();
        orderbook_thread.join();
    }
    
    void stop() {
        running_ = false;
    }

private:
    SharedMemoryManager<SharedOrderBook> orderbook_shm_;
    SharedMemoryManager<SharedMetrics> metrics_shm_;
    SharedMemoryManager<SharedTrades> trades_shm_;
    
    OrderBook order_book_;
    MetricsCollector metrics_collector_;
    
    std::atomic<bool> running_;
    std::atomic<uint64_t> next_order_id_{1};
    
    void handle_trade(const Trade& trade) {
        auto* shared_trades = trades_shm_.get();
        if (shared_trades) {
            shared_trades->push(trade);
        }
        metrics_collector_.increment_trades_executed();
    }
    
    void update_metrics() {
        auto metrics = metrics_collector_.get_current_metrics();
        auto* shared_metrics = metrics_shm_.get();
        if (shared_metrics) {
            shared_metrics->sequence_number.fetch_add(1);
            shared_metrics->metrics = metrics;
            shared_metrics->ready.store(true);
        }
    }
    
    void simulate_order_flow() {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<> price_dist(50000, 60000);
        std::uniform_int_distribution<> qty_dist(1, 100);
        std::uniform_int_distribution<> side_dist(0, 1);
        
        while (running_) {
            auto start_time = std::chrono::high_resolution_clock::now();
            
            // Generate random order
            OrderId id = next_order_id_.fetch_add(1);
            Price price = static_cast<Price>(price_dist(gen) * 100); // Price in cents
            Quantity quantity = qty_dist(gen);
            OrderSide side = static_cast<OrderSide>(side_dist(gen));
            
            Order order(id, price, quantity, side, OrderType::LIMIT, "BTCUSD");
            order_book_.add_order(order);
            
            auto end_time = std::chrono::high_resolution_clock::now();
            auto latency = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();
            
            metrics_collector_.record_latency(latency);
            metrics_collector_.increment_orders_processed();
            
            // Random delay between orders (1-10ms)
            std::this_thread::sleep_for(std::chrono::microseconds(1000 + (gen() % 9000)));
        }
    }
};

} // namespace hft

static hft::TradingEngine* g_engine = nullptr;

void signal_handler(int signal) {
    if (g_engine) {
        g_engine->stop();
    }
}

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    try {
        hft::TradingEngine engine;
        g_engine = &engine;
        engine.run();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}