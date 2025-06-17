#pragma once

#include "types.h"
#include <map>
#include <unordered_map>
#include <vector>
#include <functional>

namespace hft {

class OrderBook {
public:
    using TradeCallback = std::function<void(const Trade&)>;
    
    OrderBook(const std::string& symbol);
    
    void add_order(const Order& order);
    void cancel_order(OrderId order_id);
    void modify_order(OrderId order_id, Price new_price, Quantity new_quantity);
    
    OrderBookSnapshot get_snapshot() const;
    
    void set_trade_callback(TradeCallback callback) { trade_callback_ = callback; }
    
    double get_mid_price() const;
    double get_spread() const;
    
private:
    struct OrderBookEntry {
        Price price;
        Quantity total_quantity;
        std::vector<Order> orders;
        
        OrderBookEntry(Price p) : price(p), total_quantity(0) {}
    };
    
    using BidMap = std::map<Price, OrderBookEntry, std::greater<Price>>;
    using AskMap = std::map<Price, OrderBookEntry>;
    
    std::string symbol_;
    BidMap bids_;
    AskMap asks_;
    std::unordered_map<OrderId, Order> order_lookup_;
    TradeCallback trade_callback_;
    
    void match_orders();
    void execute_trade(const Order& buy_order, const Order& sell_order, Price price, Quantity quantity);
    void remove_order_from_book(const Order& order);
};

}