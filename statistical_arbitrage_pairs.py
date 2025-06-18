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
            return self._generate_mock_data(symbol, days_back)
        
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
            'EURCHF': 0.9500
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        
        # Generate correlated price movements
        # Create realistic intraday volatility patterns
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(days=days_back),
            periods=num_bars,
            freq='1min'
        )
        
        # Generate price series with mean reversion and volatility clustering
        returns = np.random.normal(0, 0.0001, num_bars)  # Low volatility for forex
        
        # Add some trend and mean reversion
        for i in range(1, len(returns)):
            # Mean reversion component
            returns[i] += -0.001 * returns[i-1] if abs(returns[i-1]) > 0.0005 else 0
            
            # Add some autocorrelation for realistic price action
            if i > 10:
                returns[i] += 0.1 * np.mean(returns[i-10:i])
        
        # Convert to prices
        prices = base_price * np.exp(np.cumsum(returns))
        
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
            price_series[symbol] = df.set_index('timestamp')['close']
        
        # Create combined DataFrame
        combined_df = pd.DataFrame(price_series)
        
        # Compute correlation matrix
        self.correlation_matrix = combined_df.corr()
        
        print("✅ Correlation matrix computed\\n")
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
            price_series[symbol] = df.set_index('timestamp')['close']
        
        combined_df = pd.DataFrame(price_series).dropna()
        
        results = []
        total_pairs = len(list(combinations(self.symbols, 2)))
        current_pair = 0
        
        for symbol1, symbol2 in combinations(self.symbols, 2):
            current_pair += 1
            print(f"  ↳ Testing {symbol1}/{symbol2} ({current_pair}/{total_pairs})")
            
            if symbol1 not in combined_df.columns or symbol2 not in combined_df.columns:
                continue
            
            y = combined_df[symbol1].values
            x = combined_df[symbol2].values
            
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
        print(f"   📈 Success rate: {cointegrated_count/len(results)*100:.1f}%\\n")
        
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
        df_output.to_csv(filename, index=False)
        
        print(f"💾 Results saved to {filename}")
        print(f"📈 Top 3 pairs:")
        for i, row in df_output.head(3).iterrows():
            print(f"   {i+1}. {row['pair']} - Score: {row['composite_score']:.4f}, p-value: {row['p_value']:.6f}")


def main():
    """
    Main execution function for the statistical arbitrage analysis.
    """
    print("🚀 Statistical Arbitrage HFT Strategy - Pair Identification")
    print("=" * 60)
    
    # Configuration
    SYMBOLS = ['EURUSD', 'USDCHF', 'GBPUSD', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURCHF']
    DAYS_BACK = 90
    SIGNIFICANCE_LEVEL = 0.05
    
    print(f"🎯 Target symbols: {', '.join(SYMBOLS)}")
    print(f"📅 Analysis period: {DAYS_BACK} days")
    print(f"📊 Significance level: {SIGNIFICANCE_LEVEL}\\n")
    
    # Initialize data client (demo mode for this example)
    # For production, set demo_mode=False and provide API key
    client = cTraderDataClient(demo_mode=True)
    
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