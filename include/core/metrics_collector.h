#pragma once

#include "types.h"
#include <chrono>
#include <atomic>
#include <vector>
#include <mutex>

namespace hft {

class MetricsCollector {
public:
    MetricsCollector();
    
    void record_latency(uint64_t latency_ns);
    void increment_orders_processed();
    void increment_trades_executed();
    void update_system_metrics();
    
    SystemMetrics get_current_metrics() const;
    std::vector<uint64_t> get_latency_histogram() const;
    
private:
    mutable std::mutex metrics_mutex_;
    
    std::atomic<uint32_t> orders_processed_{0};
    std::atomic<uint32_t> trades_executed_{0};
    
    std::atomic<uint64_t> total_latency_ns_{0};
    std::atomic<uint64_t> min_latency_ns_{UINT64_MAX};
    std::atomic<uint64_t> max_latency_ns_{0};
    std::atomic<uint32_t> latency_samples_{0};
    
    // Latency histogram (buckets in nanoseconds)
    static constexpr size_t HISTOGRAM_BUCKETS = 50;
    static constexpr uint64_t MAX_LATENCY_NS = 1000000; // 1ms
    std::array<std::atomic<uint32_t>, HISTOGRAM_BUCKETS> latency_histogram_;
    
    uint64_t get_cpu_usage() const;
    uint64_t get_memory_usage() const;
    std::pair<uint64_t, uint64_t> get_network_stats() const;
};

}