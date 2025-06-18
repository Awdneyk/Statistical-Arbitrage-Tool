# Statistical Arbitrage HFT Strategy

A quantitative trading system for identifying cointegrated currency pairs and executing statistical arbitrage strategies using the cTrader Open API.

## 🎯 Overview

This project implements a statistical arbitrage strategy that:
- Identifies cointegrated trading pairs from forex markets
- Connects to cTrader Open API for real-time and historical data
- Performs Engle-Granger cointegration tests
- Ranks pairs by statistical significance and trading potential
- Provides visualization and analysis tools

## 🚀 Features

### Core Functionality
- ✅ **cTrader API Integration** - Connect to cTrader Open API or FIX API
- ✅ **Historical Data Fetching** - Pull 1-minute forex data for 90+ days
- ✅ **Cointegration Testing** - Engle-Granger statistical tests
- ✅ **Correlation Analysis** - Pearson correlation matrices with heatmaps
- ✅ **Pair Ranking** - Composite scoring system for trade selection
- ✅ **Automated Reporting** - CSV exports and visualization

### Statistical Methods
- **Engle-Granger Cointegration Test** - Identifies long-term equilibrium relationships
- **Hedge Ratio Calculation** - OLS regression for optimal position sizing
- **Residual Analysis** - Spread stability and mean reversion properties
- **Composite Scoring** - Multi-factor ranking system

## 📦 Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Dependencies
- `pandas>=1.5.0` - Data manipulation and analysis
- `numpy>=1.21.0` - Numerical computing
- `statsmodels>=0.14.0` - Statistical testing
- `scipy>=1.9.0` - Scientific computing
- `scikit-learn>=1.1.0` - Machine learning utilities
- `matplotlib>=3.5.0` - Plotting and visualization
- `seaborn>=0.11.0` - Statistical data visualization
- `requests>=2.28.0` - HTTP requests for API calls

## 🔧 Configuration

### API Setup
1. **Get cTrader API Credentials**
   ```python
   # In config.py
   CTRADER_CONFIG = {
       'api_key': 'your_ctrader_api_key_here',
       'base_url': 'https://api.ctrader.com/v1',
       'demo_mode': False,  # Set to True for testing
   }
   ```

2. **Configure Symbol Lists**
   ```python
   FOREX_MAJORS = ['EURUSD', 'GBPUSD', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
   ```

## 🏃‍♂️ Quick Start

### Basic Usage
```python
from statistical_arbitrage_pairs import cTraderDataClient, StatisticalArbitrageAnalyzer

# Initialize client (demo mode for testing)
client = cTraderDataClient(demo_mode=True)

# Set up analyzer
symbols = ['EURUSD', 'USDCHF', 'GBPUSD', 'AUDUSD']
analyzer = StatisticalArbitrageAnalyzer(symbols, client)

# Run analysis
analyzer.get_data(days_back=90)
analyzer.test_cointegration()
analyzer.save_results("pairs.csv")
analyzer.plot_correlation_heatmap()
```

### Command Line Execution
```bash
# Run main analysis
python statistical_arbitrage_pairs.py

# Run examples
python example_usage.py
```

## 📊 Output Files

### Cointegrated Pairs CSV
The main output file `cointegrated_pairs.csv` contains:

| Column | Description |
|--------|-------------|
| `pair` | Trading pair (e.g., "EURUSD/USDCHF") |
| `p_value` | Cointegration test p-value |
| `hedge_ratio` | Optimal hedge ratio from OLS regression |
| `r_squared` | Goodness of fit (R²) |
| `correlation` | Pearson correlation coefficient |
| `composite_score` | Ranking score (0-1, higher is better) |

### Visualization Output
- `correlation_heatmap.png` - Correlation matrix visualization
- `residuals_plot.png` - Spread residuals analysis (if generated)

## 🔬 Statistical Methodology

### Cointegration Testing
1. **Engle-Granger Two-Step Method**
   - Step 1: Estimate long-run relationship via OLS
   - Step 2: Test residuals for unit root (ADF test)
   - Null hypothesis: No cointegration (p > 0.05)

2. **Hedge Ratio Calculation**
   ```
   Y(t) = α + β * X(t) + ε(t)
   ```
   Where β is the hedge ratio for pair (X,Y)

3. **Composite Scoring**
   ```
   Score = 0.4 * (1-p_value) + 0.3 * R² + 0.2 * |correlation| + 0.1 * stability
   ```

## 📈 Trading Strategy Implementation

### Entry/Exit Signals
```python
# Z-score based signals
z_score = (spread - spread.mean()) / spread.std()

# Entry signals
if z_score > 2.0:    # Short the spread
    # Sell Y, Buy X
elif z_score < -2.0: # Long the spread  
    # Buy Y, Sell X

# Exit signals
if abs(z_score) < 0.5:
    # Close positions
```

### Risk Management
- **Position Sizing**: Based on volatility and correlation
- **Stop Loss**: Z-score > 3.0 threshold
- **Maximum Exposure**: 50% of capital across all pairs

## 🧪 Testing and Validation

### Demo Mode
The system includes a mock data generator for testing:
```python
client = cTraderDataClient(demo_mode=True)
```

### Backtesting Preparation
```python
# Generate backtest data
python example_usage.py
# Creates backtest_data_EURUSD_USDCHF.csv
```

### Validation Methods
- **Out-of-sample testing** - Use 80/20 split for validation
- **Rolling window analysis** - Test stability over time
- **Monte Carlo simulation** - Stress test strategies

## 📁 Project Structure

```
Statistical-Arbitrage-Tool/
├── statistical_arbitrage_pairs.py    # Main analysis script
├── config.py                         # Configuration settings
├── example_usage.py                  # Usage examples
├── requirements.txt                  # Dependencies
├── README.md                         # Documentation
├── cointegrated_pairs.csv           # Output: ranked pairs
├── correlation_heatmap.png          # Output: correlation viz
└── backtest_data_*.csv              # Output: backtest data
```

## 🔌 cTrader API Integration

### Real API Implementation
For production use, replace the mock client with real cTrader API calls:

```python
def get_historical_data(self, symbol: str, timeframe: str = "M1", days_back: int = 90):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days_back)
    
    params = {
        'symbol': symbol,
        'timeframe': timeframe,
        'from': int(start_time.timestamp()),
        'to': int(end_time.timestamp()),
    }
    
    headers = {
        'Authorization': f'Bearer {self.api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{self.base_url}/historical", 
                          params=params, headers=headers)
    
    return pd.DataFrame(response.json()['bars'])
```

## ⚡ Performance Optimization

### Data Processing
- **Vectorized Operations**: Use pandas/numpy for speed
- **Memory Management**: Process data in chunks for large datasets
- **Caching**: Store intermediate results to avoid recomputation

### Statistical Optimization
- **Parallel Processing**: Test multiple pairs simultaneously
- **Incremental Updates**: Update cointegration tests as new data arrives
- **Smart Filtering**: Pre-filter pairs by correlation before cointegration testing

## 🚨 Risk Considerations

### Statistical Risks
- **Model Risk**: Cointegration relationships can break down
- **Overfitting**: Multiple testing increases false discovery rate
- **Non-stationarity**: Market regimes can change

### Operational Risks
- **API Limits**: Rate limiting and data availability
- **Execution Risk**: Slippage and latency in HFT environment
- **Technology Risk**: System failures and connectivity issues

## 📝 Future Enhancements

### Advanced Features
- [ ] **Real-time Signal Generation** - Live trading signals
- [ ] **Multi-timeframe Analysis** - Confirm signals across timeframes
- [ ] **Machine Learning Integration** - Enhance pair selection
- [ ] **Regime Detection** - Identify market state changes
- [ ] **Portfolio Optimization** - Optimal allocation across pairs

### Infrastructure
- [ ] **Database Integration** - Store historical analysis results
- [ ] **Web Dashboard** - Real-time monitoring interface
- [ ] **Alert System** - Automated trade notifications
- [ ] **Backtesting Engine** - Complete strategy testing framework

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Create an issue in the GitHub repository
- Email: [your-email@example.com]

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.