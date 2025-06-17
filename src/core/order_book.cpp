#include "core/order_book.h"
#include <algorithm>
#include <cstring>

namespace hft {

OrderBook::OrderBook(const std::string& symbol) : symbol_(symbol) {}

void OrderBook::add_order(const Order& order) {
    order_lookup_[order.id] = order;
    
    if (order.side == OrderSide::BUY) {
        auto& entry = bids_[order.price];
        if (entry.orders.empty()) {
            entry = OrderBookEntry(order.price);
        }
        entry.orders.push_back(order);
        entry.total_quantity += order.quantity;
    } else {
        auto& entry = asks_[order.price];
        if (entry.orders.empty()) {
            entry = OrderBookEntry(order.price);
        }
        entry.orders.push_back(order);
        entry.total_quantity += order.quantity;
    }
    
    match_orders();
}

void OrderBook::cancel_order(OrderId order_id) {
    auto it = order_lookup_.find(order_id);
    if (it != order_lookup_.end()) {
        remove_order_from_book(it->second);
        order_lookup_.erase(it);
    }
}

void OrderBook::modify_order(OrderId order_id, Price new_price, Quantity new_quantity) {
    auto it = order_lookup_.find(order_id);
    if (it != order_lookup_.end()) {
        Order old_order = it->second;
        remove_order_from_book(old_order);
        
        Order new_order = old_order;
        new_order.price = new_price;
        new_order.quantity = new_quantity;
        new_order.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch();
        
        add_order(new_order);
    }
}

void OrderBook::match_orders() {
    while (!bids_.empty() && !asks_.empty()) {
        auto& best_bid = bids_.begin()->second;
        auto& best_ask = asks_.begin()->second;
        
        if (best_bid.price < best_ask.price) {
            break;
        }
        
        auto& buy_order = best_bid.orders.front();
        auto& sell_order = best_ask.orders.front();
        
        Price trade_price = (buy_order.timestamp < sell_order.timestamp) ? buy_order.price : sell_order.price;
        Quantity trade_quantity = std::min(buy_order.quantity, sell_order.quantity);
        
        execute_trade(buy_order, sell_order, trade_price, trade_quantity);
        
        // Update quantities
        const_cast<Order&>(buy_order).quantity -= trade_quantity;
        const_cast<Order&>(sell_order).quantity -= trade_quantity;
        best_bid.total_quantity -= trade_quantity;
        best_ask.total_quantity -= trade_quantity;
        
        // Remove filled orders
        if (buy_order.quantity == 0) {
            order_lookup_.erase(buy_order.id);
            best_bid.orders.erase(best_bid.orders.begin());
            if (best_bid.orders.empty()) {
                bids_.erase(bids_.begin());
            }
        }
        
        if (sell_order.quantity == 0) {
            order_lookup_.erase(sell_order.id);
            best_ask.orders.erase(best_ask.orders.begin());
            if (best_ask.orders.empty()) {
                asks_.erase(asks_.begin());
            }
        }
    }
}

void OrderBook::execute_trade(const Order& buy_order, const Order& sell_order, Price price, Quantity quantity) {
    if (trade_callback_) {
        Trade trade;
        trade.buy_order_id = buy_order.id;
        trade.sell_order_id = sell_order.id;
        trade.price = price;
        trade.quantity = quantity;
        trade.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch();
        std::strncpy(trade.symbol, symbol_.c_str(), sizeof(trade.symbol) - 1);
        trade.symbol[sizeof(trade.symbol) - 1] = '\0';
        
        trade_callback_(trade);
    }
}

void OrderBook::remove_order_from_book(const Order& order) {
    if (order.side == OrderSide::BUY) {
        auto it = bids_.find(order.price);
        if (it != bids_.end()) {
            auto& orders = it->second.orders;
            auto order_it = std::find_if(orders.begin(), orders.end(),
                [&order](const Order& o) { return o.id == order.id; });
            if (order_it != orders.end()) {
                it->second.total_quantity -= order_it->quantity;
                orders.erase(order_it);
                if (orders.empty()) {
                    bids_.erase(it);
                }
            }
        }
    } else {
        auto it = asks_.find(order.price);
        if (it != asks_.end()) {
            auto& orders = it->second.orders;
            auto order_it = std::find_if(orders.begin(), orders.end(),
                [&order](const Order& o) { return o.id == order.id; });
            if (order_it != orders.end()) {
                it->second.total_quantity -= order_it->quantity;
                orders.erase(order_it);
                if (orders.empty()) {
                    asks_.erase(it);
                }
            }
        }
    }
}

OrderBookSnapshot OrderBook::get_snapshot() const {
    OrderBookSnapshot snapshot;
    std::strncpy(snapshot.symbol, symbol_.c_str(), sizeof(snapshot.symbol) - 1);
    snapshot.symbol[sizeof(snapshot.symbol) - 1] = '\0';
    snapshot.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch();
    
    // Fill bids
    snapshot.bid_count = 0;
    for (const auto& [price, entry] : bids_) {
        if (snapshot.bid_count >= MAX_BOOK_LEVELS) break;
        snapshot.bids[snapshot.bid_count] = {price, entry.total_quantity, static_cast<uint32_t>(entry.orders.size())};
        snapshot.bid_count++;
    }
    
    // Fill asks
    snapshot.ask_count = 0;
    for (const auto& [price, entry] : asks_) {
        if (snapshot.ask_count >= MAX_BOOK_LEVELS) break;
        snapshot.asks[snapshot.ask_count] = {price, entry.total_quantity, static_cast<uint32_t>(entry.orders.size())};
        snapshot.ask_count++;
    }
    
    return snapshot;
}

double OrderBook::get_mid_price() const {
    if (bids_.empty() || asks_.empty()) {
        return 0.0;
    }
    return (bids_.begin()->first + asks_.begin()->first) / 2.0;
}

double OrderBook::get_spread() const {
    if (bids_.empty() || asks_.empty()) {
        return 0.0;
    }
    return asks_.begin()->first - bids_.begin()->first;
}

}