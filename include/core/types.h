#pragma once

#include <cstdint>
#include <chrono>
#include <string>
#include <array>

namespace hft {

using Price = int64_t;
using Quantity = uint32_t;
using OrderId = uint64_t;
using Timestamp = std::chrono::nanoseconds;

enum class OrderSide : uint8_t {
    BUY = 0,
    SELL = 1
};

enum class OrderType : uint8_t {
    MARKET = 0,
    LIMIT = 1,
    STOP = 2
};

struct Order {
    OrderId id;
    Price price;
    Quantity quantity;
    OrderSide side;
    OrderType type;
    Timestamp timestamp;
    char symbol[16];
    
    Order() = default;
    Order(OrderId id, Price price, Quantity qty, OrderSide side, OrderType type, const std::string& sym)
        : id(id), price(price), quantity(qty), side(side), type(type), 
          timestamp(std::chrono::high_resolution_clock::now().time_since_epoch()) {
        std::strncpy(symbol, sym.c_str(), sizeof(symbol) - 1);
        symbol[sizeof(symbol) - 1] = '\0';
    }
};

struct Trade {
    OrderId buy_order_id;
    OrderId sell_order_id;
    Price price;
    Quantity quantity;
    Timestamp timestamp;
    char symbol[16];
};

struct BookLevel {
    Price price;
    Quantity quantity;
    uint32_t order_count;
};

constexpr size_t MAX_BOOK_LEVELS = 20;

struct OrderBookSnapshot {
    char symbol[16];
    Timestamp timestamp;
    std::array<BookLevel, MAX_BOOK_LEVELS> bids;
    std::array<BookLevel, MAX_BOOK_LEVELS> asks;
    uint32_t bid_count;
    uint32_t ask_count;
};

struct SystemMetrics {
    Timestamp timestamp;
    double cpu_usage;
    uint64_t memory_usage_bytes;
    uint64_t network_bytes_sent;
    uint64_t network_bytes_recv;
    uint32_t orders_processed;
    uint32_t trades_executed;
    uint64_t avg_latency_ns;
    uint64_t max_latency_ns;
    uint64_t min_latency_ns;
};

}