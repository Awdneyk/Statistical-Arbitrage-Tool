"""
Configuration file for Statistical Arbitrage Strategy
"""

# cTrader API Configuration
# NOTE: Replace with your actual cTrader API credentials
CTRADER_CONFIG = {
    'client_id': 'YOUR_CTRADER_CLIENT_ID',
    'client_secret': 'YOUR_CTRADER_CLIENT_SECRET',
    'base_url': 'https://api.ctrader.com/v1',
    'demo_mode': True,  # Set to False for live trading
    'timeout': 30,
    'max_retries': 3
}

# Trading Symbols Configuration
FOREX_MAJORS = [
    'EURUSD', 'GBPUSD', 'USDCHF', 'AUDUSD', 
    'USDCAD', 'NZDUSD', 'USDJPY'
]

FOREX_CROSSES = [
    'EURGBP', 'EURCHF', 'EURJPY', 'GBPCHF', 
    'GBPJPY', 'CHFJPY', 'AUDCAD', 'AUDCHF'
]

EXOTIC_PAIRS = [
    'USDTRY', 'USDZAR', 'USDMXN', 'EURTRY',
    'GBPTRY', 'USDSEK', 'USDNOK', 'USDDKK'
]

# Analysis Parameters
ANALYSIS_CONFIG = {
    'lookback_days': 90,
    'timeframe': 'M1',  # 1-minute bars
    'cointegration_pvalue_threshold': 0.05,
    'correlation_threshold': 0.7,
    'min_observations': 1000,
    'test_ratio': 0.8  # 80% for cointegration test, 20% for validation
}

# Strategy Parameters
STRATEGY_CONFIG = {
    'entry_zscore_threshold': 2.0,
    'exit_zscore_threshold': 0.5,
    'stop_loss_zscore': 3.0,
    'position_size_pct': 0.1,  # 10% of capital per trade
    'max_positions': 5,
    'rebalance_frequency': '1H'  # Hourly rebalancing
}

# Risk Management
RISK_CONFIG = {
    'max_daily_loss_pct': 0.02,  # 2% max daily loss
    'max_total_exposure': 0.5,   # 50% max total exposure
    'var_confidence': 0.95,      # 95% VaR confidence
    'lookback_var_days': 30      # 30-day VaR lookback
}