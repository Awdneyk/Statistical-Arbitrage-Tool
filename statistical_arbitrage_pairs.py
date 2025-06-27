#!/usr/bin/env python3
"""
Statistical Arbitrage HFT Strategy - Cointegrated Pairs Identification

This script identifies cointegrated and highly correlated trading pairs from 
cTrader Open API data for statistical arbitrage opportunities.

Author: Quantitative Developer
Date: 2025-06-18
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Statistical libraries
from statsmodels.tsa.stattools import coint
from sklearn.linear_model import LinearRegression
import scipy.stats as stats

# For API connections (mock implementation included)
import requests
import json
from typing import List, Dict, Tuple, Optional
import time

class cTraderDataClient:
    """
    cTrader Open API client for fetching historical price data.
    
    Note: This is a simplified implementation. In production, you would use
    the official cTrader Open API SDK or FIX API wrapper.
    """
    
    def __init__(self, api_key: str = None, demo_mode: bool = True):
        """
        Initialize cTrader API client.
        
        Args:
            api_key: Your cTrader API key
            demo_mode: If True, uses simulated data instead of real API calls
        """
        self.api_key = api_key
        self.demo_mode = demo_mode
        self.base_url = "https://api.ctrader.com/v1"  # Example URL
        
        if not demo_mode and not api_key:
            raise ValueError("API key required for live data access")
    
    def get_historical_data(self, symbol: str, timeframe: str = "M1", 
                          days_back: int = 90) -> pd.DataFrame:
        """
        Fetch historical price data for a given symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe for data (M1 = 1 minute)
            days_back: Number of days of historical data
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if self.demo_mode:
            print(f"    📝 Generating mock data for {symbol}...")
            mock_data = self._generate_mock_data(symbol, days_back)
            print(f"    ✅ Generated {len(mock_data)} bars for {symbol}")
            return mock_data
        
        # Real API implementation would go here
        # Example structure:
        """
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
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['bars'])
        else:
            raise Exception(f"API Error: {response.status_code}")
        """
        
        # For now, return mock data
        return self._generate_mock_data(symbol, days_back)
    
    def _generate_mock_data(self, symbol: str, days_back: int) -> pd.DataFrame:
        """
        Generate realistic mock price data for testing.
        
        This simulates real forex price movements with proper correlations
        between major currency pairs.
        """
        # Number of 1-minute bars in the specified period
        num_bars = days_back * 24 * 60
        
        # Use same timestamps for all symbols but different price seeds
        # This ensures all symbols have the same time index for correlation analysis
        if not hasattr(self, '_base_timestamps') or len(self._base_timestamps) != num_bars:
            self._base_timestamps = pd.date_range(
                start=datetime.now() - timedelta(days=days_back),
                periods=num_bars,
                freq='1min'
            )
        
        timestamps = self._base_timestamps
        
        # Set random seed based on symbol for reproducible results
        np.random.seed(hash(symbol) % (2**32))
        
        # Define base prices for different symbols
        base_prices = {
            'EURUSD': 1.0850,
            'USDCHF': 0.8750,
            'GBPUSD': 1.2650,
            'AUDUSD': 0.6750,
            'USDCAD': 1.3450,
            'NZDUSD': 0.6150,
            'EURCHF': 0.9500,
            'BTCUSD': 45000.0,
            'ETHUSD': 2800.0,
            'SPX500': 4800.0,
            'USDJPY': 150.0,
            'RDS.A': 65.0,      # Royal Dutch Shell A
            'RDS.B': 64.8,      # Royal Dutch Shell B (slight discount)
            'GLD': 185.0,       # Gold ETF
            'GDX': 28.0,        # Gold miners ETF
            'SPY': 480.0,       # S&P 500 ETF
            'IVV': 479.5,       # S&P 500 ETF (similar to SPY)
            'AAPL': 190.0,      # Apple
            'MSFT': 420.0,      # Microsoft
            'GOOGL': 140.0,     # Google
            'META': 310.0,      # Meta (Facebook)
            'CSCO': 52.0,       # Cisco
            'JNPR': 37.0        # Juniper Networks
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        
        # Generate price series with mean reversion and volatility clustering
        # Adjust volatility based on symbol characteristics
        volatility_map = {
            'EURUSD': 0.00008,   # Lower volatility major pair
            'USDCHF': 0.00009, 
            'GBPUSD': 0.00012,   # Higher volatility 
            'AUDUSD': 0.00010,
            'USDCAD': 0.00009,
            'NZDUSD': 0.00011,
            'EURCHF': 0.00007,   # Very low volatility cross
            'BTCUSD': 0.008,     # High volatility crypto
            'ETHUSD': 0.012,     # Very high volatility crypto
            'SPX500': 0.0015,    # Stock index volatility
            'USDJPY': 0.0001,    # Forex pair volatility
            'RDS.A': 0.002,      # Oil stock volatility
            'RDS.B': 0.002,      # Oil stock volatility (similar to RDS.A)
            'GLD': 0.0012,       # Gold ETF volatility
            'GDX': 0.003,        # Gold miners volatility (higher than gold)
            'SPY': 0.0013,       # S&P 500 ETF volatility
            'IVV': 0.0013,       # S&P 500 ETF volatility (same as SPY)
            'AAPL': 0.0025,      # Apple volatility
            'MSFT': 0.0020,      # Microsoft volatility
            'GOOGL': 0.0030,     # Google volatility
            'META': 0.0035,      # Meta volatility (higher)
            'CSCO': 0.0022,      # Cisco volatility
            'JNPR': 0.0028       # Juniper volatility (smaller cap)
        }
        
        vol = volatility_map.get(symbol, 0.0001)
        returns = np.random.normal(0, vol, num_bars)
        
        # Create more realistic correlations between USD pairs
        if 'USD' in symbol:
            # Add common USD factor
            usd_factor = np.random.normal(0, vol * 0.3, num_bars)
            if symbol.startswith('USD'):
                returns += usd_factor
            else:
                returns -= usd_factor  # Inverse correlation for XXX/USD pairs
        
        # Add some trend and mean reversion
        for i in range(1, len(returns)):
            # Mean reversion component - stronger for larger moves
            if abs(returns[i-1]) > 2 * vol:
                returns[i] += -0.3 * returns[i-1]
            
            # Add some autocorrelation for realistic price action
            if i > 5:
                returns[i] += 0.05 * np.mean(returns[i-5:i])
        
        # Ensure no extreme outliers
        returns = np.clip(returns, -5*vol, 5*vol)
        
        # Convert to prices
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Ensure prices don't go negative or too extreme
        prices = np.maximum(prices, base_price * 0.5)
        prices = np.minimum(prices, base_price * 2.0)
        
        # Generate OHLC data
        df = pd.DataFrame({
            'timestamp': timestamps,
            'close': prices
        })
        
        # Add simple OHLC based on close prices
        df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.0002, len(df)))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.0002, len(df)))
        df['volume'] = np.random.uniform(1000, 10000, len(df))
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]


class StatisticalArbitrageAnalyzer:
    """
    Main class for identifying cointegrated and correlated trading pairs.
    """
    
    def __init__(self, symbols: List[str], data_client: cTraderDataClient):
        """
        Initialize the analyzer.
        
        Args:
            symbols: List of trading symbols to analyze
            data_client: cTrader data client instance
        """
        self.symbols = symbols
        self.data_client = data_client
        self.price_data = {}
        self.correlation_matrix = None
        self.cointegration_results = []
    
    def get_data(self, days_back: int = 90) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for all symbols.
        
        Args:
            days_back: Number of days of historical data to fetch
            
        Returns:
            Dictionary mapping symbols to their price DataFrames
        """
        print("📊 Fetching historical data...")
        
        for symbol in self.symbols:
            print(f"  ↳ Downloading {symbol}...")
            try:
                df = self.data_client.get_historical_data(symbol, days_back=days_back)
                self.price_data[symbol] = df
                print(f"    ✅ {len(df)} bars retrieved")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"    ❌ Error fetching {symbol}: {e}")
                continue
        
        print(f"✅ Data collection completed for {len(self.price_data)} symbols\\n")
        return self.price_data
    
    def compute_correlation_matrix(self) -> pd.DataFrame:
        """
        Compute correlation matrix for all symbol pairs.
        
        Returns:
            Correlation matrix as DataFrame
        """
        print("📈 Computing correlation matrix...")
        
        # Align all price series by timestamp
        price_series = {}
        for symbol, df in self.price_data.items():
            print(f"    🔍 Processing {symbol}: {len(df) if df is not None else 0} rows")
            if df is None or df.empty:
                print(f"    ⚠️  Skipping {symbol} - no data for correlation")
                continue
            try:
                print(f"    📊 Columns in {symbol}: {list(df.columns)}")
                price_series[symbol] = df.set_index('timestamp')['close']
                print(f"    ✅ {symbol} processed: {len(price_series[symbol])} price points")
            except Exception as e:
                print(f"    ⚠️  Error processing {symbol} for correlation: {e}")
                continue
        
        if len(price_series) < 2:
            print(f"❌ Not enough symbols for correlation matrix ({len(price_series)} available)")
            self.correlation_matrix = pd.DataFrame()
            return self.correlation_matrix
        
        # Create combined DataFrame
        print(f"    🔄 Creating combined DataFrame from {len(price_series)} series...")
        combined_df = pd.DataFrame(price_series)
        print(f"    📏 Combined DataFrame shape before dropna: {combined_df.shape}")
        print(f"    📊 Sample timestamps: {combined_df.index[:5].tolist()}")
        
        combined_df = combined_df.dropna()
        print(f"    📏 Combined DataFrame shape after dropna: {combined_df.shape}")
        
        if combined_df.empty:
            print(f"❌ No data available for correlation computation")
            self.correlation_matrix = pd.DataFrame()
            return self.correlation_matrix
        
        # Compute correlation matrix
        self.correlation_matrix = combined_df.corr()
        
        print(f"✅ Correlation matrix computed for {len(self.correlation_matrix)} symbols\\n")
        return self.correlation_matrix
    
    def test_cointegration(self, significance_level: float = 0.05) -> List[Dict]:
        """
        Test all symbol pairs for cointegration using Engle-Granger test.
        
        Args:
            significance_level: P-value threshold for statistical significance
            
        Returns:
            List of dictionaries containing cointegration test results
        """
        print("🔬 Testing cointegration for all pairs...")
        
        # Align all price series
        price_series = {}
        for symbol, df in self.price_data.items():
            if df is None or df.empty:
                print(f"    ⚠️  Skipping {symbol} - no data available")
                continue
            try:
                price_series[symbol] = df.set_index('timestamp')['close']
            except Exception as e:
                print(f"    ⚠️  Error processing {symbol}: {e}")
                continue
        
        if len(price_series) < 2:
            print(f"    ❌ Not enough symbols with valid data ({len(price_series)} available)")
            return []
        
        combined_df = pd.DataFrame(price_series).dropna()
        
        if combined_df.empty:
            print(f"    ❌ No overlapping data after alignment")
            return []
        
        print(f"    📊 Data aligned: {len(combined_df)} observations for {len(combined_df.columns)} symbols")
        
        results = []
        available_symbols = list(combined_df.columns)
        total_pairs = len(list(combinations(available_symbols, 2)))
        current_pair = 0
        
        for symbol1, symbol2 in combinations(available_symbols, 2):
            current_pair += 1
            print(f"  ↳ Testing {symbol1}/{symbol2} ({current_pair}/{total_pairs})")
            
            y = combined_df[symbol1].values
            x = combined_df[symbol2].values
            
            # Validate data quality
            if len(y) < 50 or len(x) < 50:
                print(f"    ⚠️  Insufficient data points ({len(y)} observations)")
                continue
            
            if np.all(y == y[0]) or np.all(x == x[0]):
                print(f"    ⚠️  Constant price series detected")
                continue
            
            # Perform Engle-Granger cointegration test
            try:
                coint_stat, p_value, critical_values = coint(y, x)
                
                # Calculate hedge ratio using OLS regression
                reg = LinearRegression()
                reg.fit(x.reshape(-1, 1), y)
                hedge_ratio = reg.coef_[0]
                intercept = reg.intercept_
                
                # Calculate R-squared
                r_squared = reg.score(x.reshape(-1, 1), y)
                
                # Calculate residuals for additional statistics
                residuals = y - (hedge_ratio * x + intercept)
                residual_std = np.std(residuals)
                
                result = {
                    'symbol1': symbol1,
                    'symbol2': symbol2,
                    'pair': f"{symbol1}/{symbol2}",
                    'cointegration_stat': coint_stat,
                    'p_value': p_value,
                    'critical_value_1%': critical_values[0],
                    'critical_value_5%': critical_values[1],
                    'critical_value_10%': critical_values[2],
                    'hedge_ratio': hedge_ratio,
                    'intercept': intercept,
                    'r_squared': r_squared,
                    'residual_std': residual_std,
                    'is_cointegrated': p_value < significance_level,
                    'correlation': combined_df[symbol1].corr(combined_df[symbol2])
                }
                
                results.append(result)
                
                if result['is_cointegrated']:
                    print(f"    ✅ Cointegrated (p={p_value:.4f})")
                else:
                    print(f"    ❌ Not cointegrated (p={p_value:.4f})")
                    
            except Exception as e:
                print(f"    ⚠️  Error testing {symbol1}/{symbol2}: {e}")
                continue
        
        self.cointegration_results = results
        cointegrated_count = sum(1 for r in results if r['is_cointegrated'])
        
        print(f"\\n✅ Cointegration testing completed:")
        print(f"   📊 Total pairs tested: {len(results)}")
        print(f"   🎯 Cointegrated pairs found: {cointegrated_count}")
        
        # Fix division by zero error
        if len(results) > 0:
            success_rate = cointegrated_count/len(results)*100
            print(f"   📈 Success rate: {success_rate:.1f}%\\n")
        else:
            print(f"   ⚠️  No pairs could be tested\\n")
        
        return results
    
    def rank_pairs(self) -> pd.DataFrame:
        """
        Rank pairs by cointegration strength and other criteria.
        
        Returns:
            DataFrame with ranked cointegrated pairs
        """
        print("🏆 Ranking cointegrated pairs...")
        
        # Filter only cointegrated pairs
        cointegrated_pairs = [r for r in self.cointegration_results if r['is_cointegrated']]
        
        if not cointegrated_pairs:
            print("❌ No cointegrated pairs found!")
            return pd.DataFrame()
        
        df = pd.DataFrame(cointegrated_pairs)
        
        # Create composite score for ranking
        # Lower p-value = better (more significant)
        # Higher R-squared = better (stronger relationship)
        # Lower residual std = better (more stable relationship)
        
        df['p_value_score'] = 1 - df['p_value']  # Invert p-value (higher = better)
        df['composite_score'] = (
            0.4 * df['p_value_score'] +
            0.3 * df['r_squared'] +
            0.2 * abs(df['correlation']) +
            0.1 * (1 / (1 + df['residual_std']))  # Inverse of residual std
        )
        
        # Sort by composite score (descending)
        df_ranked = df.sort_values('composite_score', ascending=False)
        
        print(f"✅ {len(df_ranked)} cointegrated pairs ranked\\n")
        return df_ranked
    
    def plot_correlation_heatmap(self, save_path: str = "correlation_heatmap.png"):
        """
        Create and save correlation heatmap.
        
        Args:
            save_path: Path to save the heatmap image
        """
        if self.correlation_matrix is None:
            self.compute_correlation_matrix()
        
        if self.correlation_matrix is None or self.correlation_matrix.empty:
            print("❌ No correlation matrix available for plotting")
            return
        
        plt.figure(figsize=(10, 8))
        mask = np.triu(np.ones_like(self.correlation_matrix, dtype=bool))
        
        sns.heatmap(
            self.correlation_matrix, 
            mask=mask,
            annot=True, 
            cmap='RdYlBu_r', 
            center=0,
            square=True,
            fmt='.3f',
            cbar_kws={"shrink": .8}
        )
        
        plt.title('Currency Pairs Correlation Matrix', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📊 Correlation heatmap saved to {save_path}")
    
    def save_results(self, filename: str = "cointegrated_pairs.csv"):
        """
        Save cointegration results to CSV file.
        
        Args:
            filename: Output CSV filename
        """
        if not self.cointegration_results:
            print("❌ No results to save. Run cointegration test first.")
            return
        
        df = self.rank_pairs()
        
        if df.empty:
            print("❌ No cointegrated pairs to save.")
            return
        
        # Select and reorder columns for output
        output_columns = [
            'pair', 'symbol1', 'symbol2', 'composite_score',
            'p_value', 'cointegration_stat', 'hedge_ratio', 
            'r_squared', 'correlation', 'residual_std',
            'critical_value_5%', 'intercept'
        ]
        
        df_output = df[output_columns].round(6)
        
        try:
            df_output.to_csv(filename, index=False)
            print(f"💾 Results saved to {filename}")
            
            print(f"📈 Top {min(3, len(df_output))} pairs:")
            for i, row in df_output.head(3).iterrows():
                print(f"   {i+1}. {row['pair']} - Score: {row['composite_score']:.4f}, p-value: {row['p_value']:.6f}")
                
        except Exception as e:
            print(f"❌ Error saving results to {filename}: {e}")


def main():
    """
    Main execution function for the statistical arbitrage analysis.
    """
    print("🚀 Statistical Arbitrage HFT Strategy - Pair Identification")
    print("=" * 60)
    
    # Configuration
    SYMBOLS = ['RDS.A', 'RDS.B', 'GLD', 'GDX', 'SPY', 'IVV', 'AAPL', 'MSFT', 'GOOGL', 'META', 'CSCO', 'JNPR', 'EURUSD', 'GBPUSD', 'USDCHF']
    DAYS_BACK = 90
    SIGNIFICANCE_LEVEL = 0.05
    
    print(f"🎯 Target symbols: {', '.join(SYMBOLS)}")
    print(f"📅 Analysis period: {DAYS_BACK} days")
    print(f"📊 Significance level: {SIGNIFICANCE_LEVEL}\\n")
    
    # Initialize data client using config
    from config import CTRADER_CONFIG
    client = cTraderDataClient(
        api_key=CTRADER_CONFIG.get('client_id'),
        demo_mode=CTRADER_CONFIG.get('demo_mode', True)
    )
    
    # Initialize analyzer
    analyzer = StatisticalArbitrageAnalyzer(SYMBOLS, client)
    
    try:
        # Step 1: Fetch historical data
        analyzer.get_data(days_back=DAYS_BACK)
        
        # Step 2: Compute correlation matrix
        analyzer.compute_correlation_matrix()
        
        # Step 3: Test for cointegration
        analyzer.test_cointegration(significance_level=SIGNIFICANCE_LEVEL)
        
        # Step 4: Rank and save results
        analyzer.save_results("cointegrated_pairs.csv")
        
        # Step 5: Create visualizations
        analyzer.plot_correlation_heatmap("correlation_heatmap.png")
        
        print("\\n🎉 Analysis completed successfully!")
        print("📁 Output files:")
        print("   • cointegrated_pairs.csv - Ranked cointegrated pairs")
        print("   • correlation_heatmap.png - Correlation visualization")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()