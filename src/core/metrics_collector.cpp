#include "core/metrics_collector.h"
#include <fstream>
#include <sstream>
#include <thread>

namespace hft {

MetricsCollector::MetricsCollector() {
    for (auto& bucket : latency_histogram_) {
        bucket.store(0);
    }
}

void MetricsCollector::record_latency(uint64_t latency_ns) {
    total_latency_ns_.fetch_add(latency_ns);
    latency_samples_.fetch_add(1);
    
    // Update min/max
    uint64_t current_min = min_latency_ns_.load();
    while (latency_ns < current_min && !min_latency_ns_.compare_exchange_weak(current_min, latency_ns)) {}
    
    uint64_t current_max = max_latency_ns_.load();
    while (latency_ns > current_max && !max_latency_ns_.compare_exchange_weak(current_max, latency_ns)) {}
    
    // Update histogram
    if (latency_ns < MAX_LATENCY_NS) {
        size_t bucket = (latency_ns * HISTOGRAM_BUCKETS) / MAX_LATENCY_NS;
        if (bucket >= HISTOGRAM_BUCKETS) bucket = HISTOGRAM_BUCKETS - 1;
        latency_histogram_[bucket].fetch_add(1);
    } else {
        latency_histogram_[HISTOGRAM_BUCKETS - 1].fetch_add(1);
    }
}

void MetricsCollector::increment_orders_processed() {
    orders_processed_.fetch_add(1);
}

void MetricsCollector::increment_trades_executed() {
    trades_executed_.fetch_add(1);
}

SystemMetrics MetricsCollector::get_current_metrics() const {
    SystemMetrics metrics;
    metrics.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch();
    metrics.cpu_usage = get_cpu_usage();
    metrics.memory_usage_bytes = get_memory_usage();
    
    auto [bytes_sent, bytes_recv] = get_network_stats();
    metrics.network_bytes_sent = bytes_sent;
    metrics.network_bytes_recv = bytes_recv;
    
    metrics.orders_processed = orders_processed_.load();
    metrics.trades_executed = trades_executed_.load();
    
    uint32_t samples = latency_samples_.load();
    if (samples > 0) {
        metrics.avg_latency_ns = total_latency_ns_.load() / samples;
        metrics.min_latency_ns = min_latency_ns_.load();
        metrics.max_latency_ns = max_latency_ns_.load();
    } else {
        metrics.avg_latency_ns = 0;
        metrics.min_latency_ns = 0;
        metrics.max_latency_ns = 0;
    }
    
    return metrics;
}

std::vector<uint64_t> MetricsCollector::get_latency_histogram() const {
    std::vector<uint64_t> histogram(HISTOGRAM_BUCKETS);
    for (size_t i = 0; i < HISTOGRAM_BUCKETS; ++i) {
        histogram[i] = latency_histogram_[i].load();
    }
    return histogram;
}

uint64_t MetricsCollector::get_cpu_usage() const {
    static uint64_t last_idle = 0, last_total = 0;
    
    std::ifstream file("/proc/stat");
    std::string line;
    if (std::getline(file, line)) {
        std::istringstream iss(line);
        std::string cpu;
        uint64_t user, nice, system, idle, iowait, irq, softirq, steal;
        iss >> cpu >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;
        
        uint64_t total_idle = idle + iowait;
        uint64_t total = user + nice + system + idle + iowait + irq + softirq + steal;
        
        uint64_t total_diff = total - last_total;
        uint64_t idle_diff = total_idle - last_idle;
        
        last_total = total;
        last_idle = total_idle;
        
        if (total_diff > 0) {
            return static_cast<uint64_t>((1000.0 * (total_diff - idle_diff)) / total_diff);
        }
    }
    return 0;
}

uint64_t MetricsCollector::get_memory_usage() const {
    std::ifstream file("/proc/self/status");
    std::string line;
    while (std::getline(file, line)) {
        if (line.substr(0, 6) == "VmRSS:") {
            std::istringstream iss(line.substr(6));
            uint64_t memory_kb;
            iss >> memory_kb;
            return memory_kb * 1024; // Convert to bytes
        }
    }
    return 0;
}

std::pair<uint64_t, uint64_t> MetricsCollector::get_network_stats() const {
    static uint64_t last_bytes_sent = 0, last_bytes_recv = 0;
    
    std::ifstream file("/proc/net/dev");
    std::string line;
    uint64_t total_bytes_recv = 0, total_bytes_sent = 0;
    
    // Skip header lines
    std::getline(file, line);
    std::getline(file, line);
    
    while (std::getline(file, line)) {
        std::istringstream iss(line);
        std::string interface;
        uint64_t bytes_recv, packets_recv, errs_recv, drop_recv, fifo_recv, frame_recv, compressed_recv, multicast_recv;
        uint64_t bytes_sent, packets_sent, errs_sent, drop_sent, fifo_sent, colls_sent, carrier_sent, compressed_sent;
        
        iss >> interface >> bytes_recv >> packets_recv >> errs_recv >> drop_recv >> fifo_recv >> frame_recv >> compressed_recv >> multicast_recv
            >> bytes_sent >> packets_sent >> errs_sent >> drop_sent >> fifo_sent >> colls_sent >> carrier_sent >> compressed_sent;
        
        if (interface.find("lo:") == std::string::npos) { // Skip loopback
            total_bytes_recv += bytes_recv;
            total_bytes_sent += bytes_sent;
        }
    }
    
    uint64_t delta_sent = total_bytes_sent - last_bytes_sent;
    uint64_t delta_recv = total_bytes_recv - last_bytes_recv;
    
    last_bytes_sent = total_bytes_sent;
    last_bytes_recv = total_bytes_recv;
    
    return {delta_sent, delta_recv};
}

}