#pragma once

#include "types.h"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <atomic>
#include <string>
#include <stdexcept>

namespace hft {

template<typename T>
class SharedMemoryManager {
public:
    SharedMemoryManager(const std::string& name, size_t size = sizeof(T))
        : name_(name), size_(size), fd_(-1), ptr_(nullptr) {}
    
    ~SharedMemoryManager() {
        cleanup();
    }
    
    void create() {
        fd_ = shm_open(name_.c_str(), O_CREAT | O_RDWR, 0666);
        if (fd_ == -1) {
            throw std::runtime_error("Failed to create shared memory: " + name_);
        }
        
        if (ftruncate(fd_, size_) == -1) {
            close(fd_);
            shm_unlink(name_.c_str());
            throw std::runtime_error("Failed to set shared memory size");
        }
        
        ptr_ = static_cast<T*>(mmap(nullptr, size_, PROT_READ | PROT_WRITE, MAP_SHARED, fd_, 0));
        if (ptr_ == MAP_FAILED) {
            close(fd_);
            shm_unlink(name_.c_str());
            throw std::runtime_error("Failed to map shared memory");
        }
        
        new(ptr_) T();
    }
    
    void open() {
        fd_ = shm_open(name_.c_str(), O_RDWR, 0666);
        if (fd_ == -1) {
            throw std::runtime_error("Failed to open shared memory: " + name_);
        }
        
        ptr_ = static_cast<T*>(mmap(nullptr, size_, PROT_READ | PROT_WRITE, MAP_SHARED, fd_, 0));
        if (ptr_ == MAP_FAILED) {
            close(fd_);
            throw std::runtime_error("Failed to map shared memory");
        }
    }
    
    T* get() const { return ptr_; }
    
    void cleanup() {
        if (ptr_ && ptr_ != MAP_FAILED) {
            munmap(ptr_, size_);
            ptr_ = nullptr;
        }
        if (fd_ != -1) {
            close(fd_);
            fd_ = -1;
        }
    }
    
    void unlink() {
        shm_unlink(name_.c_str());
    }

private:
    std::string name_;
    size_t size_;
    int fd_;
    T* ptr_;
};

struct SharedOrderBook {
    std::atomic<uint64_t> sequence_number{0};
    OrderBookSnapshot snapshot;
    std::atomic<bool> ready{false};
};

struct SharedMetrics {
    std::atomic<uint64_t> sequence_number{0};
    SystemMetrics metrics;
    std::atomic<bool> ready{false};
};

struct SharedTrades {
    static constexpr size_t MAX_TRADES = 1000;
    std::atomic<uint32_t> head{0};
    std::atomic<uint32_t> tail{0};
    std::array<Trade, MAX_TRADES> trades;
    
    bool push(const Trade& trade) {
        uint32_t current_tail = tail.load();
        uint32_t next_tail = (current_tail + 1) % MAX_TRADES;
        
        if (next_tail == head.load()) {
            return false; // Buffer full
        }
        
        trades[current_tail] = trade;
        tail.store(next_tail);
        return true;
    }
    
    bool pop(Trade& trade) {
        uint32_t current_head = head.load();
        if (current_head == tail.load()) {
            return false; // Buffer empty
        }
        
        trade = trades[current_head];
        head.store((current_head + 1) % MAX_TRADES);
        return true;
    }
};

}