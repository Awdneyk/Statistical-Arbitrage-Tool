# HFT Trading System with Real-time Monitoring

A high-performance C++ trading system with integrated web-based monitoring dashboard featuring real-time order book visualization, latency metrics, and system health indicators.

## Architecture

### Core Components

- **C++ Trading Engine**: High-performance order matching engine with shared memory interface
- **WebSocket Server**: Real-time data streaming using uWebSockets
- **React Dashboard**: Interactive web-based monitoring interface
- **Shared Memory**: Zero-copy data sharing between components

### Features

- ⚡ **Ultra-low latency** order matching engine
- 📊 **Real-time order book** visualization with D3.js
- 📈 **Live latency histogram** updating every 100ms
- 🎯 **System health monitoring** (CPU, memory, network)
- 🎮 **WebGL-accelerated 3D tick charts**
- 🐳 **Containerized deployment** with Docker

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Running the System

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Statistical-Arbitrage-Tool
   ```

2. **Build and start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the dashboard**
   Open your browser to `http://localhost`

The system will start three services:
- Trading Engine (internal, uses shared memory)
- WebSocket Server (port 8080)
- Frontend Dashboard (port 80)

### Development Setup

#### C++ Components

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get install build-essential cmake pkg-config libuv1-dev libssl-dev zlib1g-dev

# Build trading engine
mkdir build && cd build
cmake ..
make -j$(nproc)

# Run components
./trading_engine &
./websocket_server
```

#### Frontend

```bash
cd frontend
npm install
npm run dev  # Development server on port 3000
```

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Trading       │    │   WebSocket      │    │   Frontend      │
│   Engine        │◄──►│   Server         │◄──►│   Dashboard     │
│   (C++)         │    │   (C++ uWS)      │    │   (React/TS)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Memory                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐    │
│  │ Order Book  │ │   Metrics   │ │        Trades           │    │
│  │ Snapshots   │ │   Data      │ │        Feed             │    │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Features

### Ultra-Low Latency
- **Shared memory** for zero-copy data sharing
- **Lock-free data structures** for concurrent access
- **Memory-mapped files** for persistent metrics
- **SIMD optimizations** where applicable

### Real-time Monitoring
- **100ms metric updates** for latency histograms
- **10ms order book updates** via WebSocket
- **WebGL acceleration** for smooth 3D visualizations
- **Efficient D3.js rendering** for complex charts

## Dashboard Components

### Order Book Visualization
- Real-time bid/ask ladder
- Interactive price levels
- Volume-based bar sizing
- Mid-price indicator

### Latency Histogram
- Sub-microsecond precision
- Real-time distribution updates
- Statistical summaries (min/avg/max)
- Color-coded performance zones

### System Health Indicators
- CPU usage monitoring
- Memory consumption tracking
- Network I/O statistics
- Trading throughput metrics

### 3D Tick Chart
- WebGL-accelerated rendering
- Real-time trade visualization
- Multi-dimensional data (price/time/volume)
- Auto-rotating camera view

## Configuration

### Environment Variables
- `WEBSOCKET_PORT`: WebSocket server port (default: 8080)
- `FRONTEND_PORT`: Frontend port (default: 80)
- `MAX_ORDERS`: Maximum orders in memory (default: 100000)

### Shared Memory Segments
- `/hft_orderbook`: Order book snapshots
- `/hft_metrics`: System metrics
- `/hft_trades`: Trade execution feed

## Monitoring & Health Checks

### Health Endpoints
- `http://localhost/health` - Frontend health
- `http://localhost:8080/health` - WebSocket server health

### Docker Health Checks
All services include health checks with automatic restart on failure.

## Performance Tuning

### System Optimization
```bash
# Increase shared memory limits
echo 'kernel.shmmax = 268435456' >> /etc/sysctl.conf
echo 'kernel.shmall = 2097152' >> /etc/sysctl.conf

# Set CPU affinity for trading engine
taskset -c 0 ./trading_engine

# Disable CPU frequency scaling
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### Compiler Optimizations
- `-O3 -march=native -ffast-math`
- Link-time optimization enabled
- Profile-guided optimization support

## Troubleshooting

### Common Issues

1. **Shared memory permissions**
   ```bash
   sudo chmod 666 /dev/shm/hft_*
   ```

2. **WebSocket connection fails**
   - Check firewall settings
   - Verify port 8080 availability
   - Review Docker network configuration

3. **High latency measurements**
   - Check CPU frequency scaling
   - Verify NUMA topology
   - Review system load

### Logs
```bash
# View service logs
docker-compose logs trading-engine
docker-compose logs websocket-server
docker-compose logs frontend
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request