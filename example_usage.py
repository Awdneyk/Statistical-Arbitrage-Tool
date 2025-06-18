#!/usr/bin/env python3
"""
Example usage script for Statistical Arbitrage Pair Identification

This script demonstrates how to use the statistical_arbitrage_pairs.py 
module with different configurations and symbol sets.
"""

from statistical_arbitrage_pairs import cTraderDataClient, StatisticalArbitrageAnalyzer
from config import FOREX_MAJORS, FOREX_CROSSES, ANALYSIS_CONFIG
import pandas as pd

def run_basic_analysis():
    """
    Run basic cointegration analysis on major forex pairs.
    """
    print("🔍 Running Basic Analysis - Major Forex Pairs")
    print("-" * 50)
    
    # Use major forex pairs
    symbols = FOREX_MAJORS
    
    # Initialize client and analyzer
    client = cTraderDataClient(demo_mode=True)
    analyzer = StatisticalArbitrageAnalyzer(symbols, client)
    
    # Run analysis
    analyzer.get_data(days_back=30)  # Shorter period for quick test
    analyzer.compute_correlation_matrix()
    analyzer.test_cointegration(significance_level=0.05)
    
    # Get results
    results_df = analyzer.rank_pairs()
    
    if not results_df.empty:
        print(f"\\n📊 Found {len(results_df)} cointegrated pairs:")
        print(results_df[['pair', 'p_value', 'hedge_ratio', 'r_squared']].head())
    else:
        print("\\n❌ No cointegrated pairs found in this dataset")
    
    return analyzer

def run_extended_analysis():
    """
    Run extended analysis including cross pairs.
    """
    print("\\n🔍 Running Extended Analysis - Major + Cross Pairs")
    print("-" * 50)
    
    # Combine major and cross pairs
    symbols = FOREX_MAJORS + FOREX_CROSSES[:4]  # Limit for demo
    
    client = cTraderDataClient(demo_mode=True)
    analyzer = StatisticalArbitrageAnalyzer(symbols, client)
    
    # Run full analysis with visualization
    analyzer.get_data(days_back=ANALYSIS_CONFIG['lookback_days'])
    analyzer.compute_correlation_matrix()
    analyzer.test_cointegration(significance_level=ANALYSIS_CONFIG['cointegration_pvalue_threshold'])
    analyzer.save_results("extended_pairs.csv")
    analyzer.plot_correlation_heatmap("extended_correlation.png")
    
    return analyzer

def analyze_specific_pairs():
    """
    Analyze specific currency pairs of interest.
    """
    print("\\n🎯 Analyzing Specific High-Interest Pairs")
    print("-" * 50)
    
    # Focus on EUR and USD related pairs
    symbols = ['EURUSD', 'EURGBP', 'EURCHF', 'EURJPY', 'USDCHF', 'GBPUSD']
    
    client = cTraderDataClient(demo_mode=True)
    analyzer = StatisticalArbitrageAnalyzer(symbols, client)
    
    analyzer.get_data(days_back=60)
    results = analyzer.test_cointegration(significance_level=0.1)  # More lenient
    
    # Custom analysis - look at correlation patterns
    corr_matrix = analyzer.compute_correlation_matrix()
    
    print("\\n📈 High Correlation Pairs (>0.8):")
    for i, row in corr_matrix.iterrows():
        for j, col in enumerate(corr_matrix.columns):
            if i != col and abs(corr_matrix.loc[i, col]) > 0.8:
                print(f"   {i} - {col}: {corr_matrix.loc[i, col]:.3f}")
    
    return analyzer

def backtest_preparation():
    """
    Prepare data for backtesting the best pairs found.
    """
    print("\\n⚡ Preparing Data for Backtesting")
    print("-" * 50)
    
    # Run analysis to find best pairs
    symbols = FOREX_MAJORS
    client = cTraderDataClient(demo_mode=True)
    analyzer = StatisticalArbitrageAnalyzer(symbols, client)
    
    analyzer.get_data(days_back=90)
    analyzer.test_cointegration()
    ranked_pairs = analyzer.rank_pairs()
    
    if not ranked_pairs.empty:
        # Get top pair for backtesting
        top_pair = ranked_pairs.iloc[0]
        symbol1, symbol2 = top_pair['symbol1'], top_pair['symbol2']
        
        print(f"🏆 Best pair for backtesting: {symbol1}/{symbol2}")
        print(f"   P-value: {top_pair['p_value']:.6f}")
        print(f"   Hedge ratio: {top_pair['hedge_ratio']:.4f}")
        print(f"   R-squared: {top_pair['r_squared']:.4f}")
        
        # Prepare data for strategy backtesting
        price_data = {}
        for symbol in [symbol1, symbol2]:
            df = analyzer.price_data[symbol].copy()
            df['returns'] = df['close'].pct_change()
            price_data[symbol] = df
        
        # Calculate spread for backtesting
        df1 = price_data[symbol1].set_index('timestamp')
        df2 = price_data[symbol2].set_index('timestamp')
        
        spread = df1['close'] - top_pair['hedge_ratio'] * df2['close']
        spread_zscore = (spread - spread.mean()) / spread.std()
        
        print(f"\\n📊 Spread Statistics:")
        print(f"   Mean: {spread.mean():.6f}")
        print(f"   Std: {spread.std():.6f}")
        print(f"   Current Z-score: {spread_zscore.iloc[-1]:.3f}")
        
        # Save backtest data
        backtest_data = pd.DataFrame({
            f'{symbol1}_price': df1['close'],
            f'{symbol2}_price': df2['close'],
            'spread': spread,
            'spread_zscore': spread_zscore
        })
        
        backtest_data.to_csv(f"backtest_data_{symbol1}_{symbol2}.csv")
        print(f"💾 Backtest data saved to backtest_data_{symbol1}_{symbol2}.csv")
    
    return analyzer

def main():
    """
    Run all example analyses.
    """
    print("🚀 Statistical Arbitrage - Example Usage")
    print("=" * 60)
    
    try:
        # Run different types of analysis
        run_basic_analysis()
        run_extended_analysis()
        analyze_specific_pairs()
        backtest_preparation()
        
        print("\\n✅ All example analyses completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()