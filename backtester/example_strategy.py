"""
Simple example showing how to use pattern recognition strategies.

This example creates synthetic price data to demonstrate the backtester
without requiring a database connection.

Run this file to see how the double top/bottom strategy works:
    python example_strategy.py
"""

import pandas as pd
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

from src.strategies.double_top_bottom_strategy import DoubleTopBottomStrategy


def create_sample_data_with_patterns():
    """
    Create synthetic price data that contains double top and double bottom patterns.

    This allows testing the strategy without needing real market data.
    """
    # Create 500 bars of data
    np.random.seed(42)
    n_bars = 500

    # Start with a base price
    base_price = 100.0
    prices = [base_price]

    # Generate random walk with some patterns
    for i in range(1, n_bars):
        # Add some trend and noise
        change = np.random.normal(0, 0.5)

        # Inject double bottom pattern around bar 100-140
        if 100 <= i <= 120:
            change = -0.8  # Downtrend to first trough
        elif 121 <= i <= 130:
            change = 0.6   # Bounce up
        elif 131 <= i <= 150:
            change = -0.7  # Down to second trough (similar to first)
        elif 151 <= i <= 160:
            change = 1.2   # Strong breakout up (pattern confirmation)

        # Inject double top pattern around bar 250-290
        if 250 <= i <= 270:
            change = 0.8   # Uptrend to first peak
        elif 271 <= i <= 280:
            change = -0.6  # Pullback
        elif 281 <= i <= 300:
            change = 0.7   # Up to second peak (similar to first)
        elif 301 <= i <= 310:
            change = -1.2  # Strong breakdown (pattern confirmation)

        prices.append(prices[-1] + change)

    # Create OHLCV data
    data = []
    for i, close in enumerate(prices):
        # Generate realistic OHLC from close price
        high = close + abs(np.random.normal(0, 0.3))
        low = close - abs(np.random.normal(0, 0.3))
        open_price = close + np.random.normal(0, 0.2)
        volume = int(np.random.uniform(1000, 10000))

        data.append({
            'timestamp': pd.Timestamp('2024-01-01') + pd.Timedelta(hours=i),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)

    return df


def main():
    """Run example backtest with synthetic data."""
    print("=" * 70)
    print("EXAMPLE: Double Top/Bottom Pattern Recognition Strategy")
    print("=" * 70)
    print()

    # 1. Create sample data with patterns
    print("Creating synthetic price data with embedded patterns...")
    data = create_sample_data_with_patterns()
    print(f"✓ Created {len(data)} bars of data")
    print(f"  Date range: {data.index[0]} to {data.index[-1]}")
    print()

    # 2. Configure the strategy
    config = {
        'tolerance': 0.03,          # 3% tolerance for pattern matching
        'min_bars_between': 10,     # Minimum bars between peaks/troughs
        'max_bars_between': 50,     # Maximum bars between peaks/troughs
        'peak_order': 5,            # Peak detection sensitivity
        'trough_order': 5           # Trough detection sensitivity
    }

    print("Strategy Configuration:")
    for key, value in config.items():
        print(f"  - {key}: {value}")
    print()

    # 3. Initialize and run strategy
    print("Initializing strategy...")
    strategy = DoubleTopBottomStrategy(data, config=config)

    print("Running backtest...")
    print()
    results = strategy.backtest()

    # 4. Display results
    print()
    print("=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print()
    print(results.to_string())
    print()

    # 5. Show detailed summary
    print(strategy.summary())

    # 6. Show individual trades
    if strategy.portfolio:
        trade_log = strategy.portfolio.get_trade_log()

        if len(trade_log) > 0:
            print("=" * 70)
            print("INDIVIDUAL TRADES")
            print("=" * 70)
            print()
            print(trade_log.to_string())
            print()

            # Show buy and sell signals
            signals = strategy.get_signals_dataframe()
            buy_count = signals['buy'].sum()
            sell_count = signals['sell'].sum()

            print(f"Buy signals (double bottoms detected): {buy_count}")
            print(f"Sell signals (double tops detected): {sell_count}")
            print()

            if buy_count > 0:
                print("Buy signal timestamps:")
                print(signals[signals['buy']].index.tolist())
                print()

            if sell_count > 0:
                print("Sell signal timestamps:")
                print(signals[signals['sell']].index.tolist())
                print()
        else:
            print("⚠ No trades were executed.")
            print("  Try adjusting the strategy parameters (tolerance, min/max bars, order)")
            print()

    # 7. Interpret results
    print("=" * 70)
    print("HOW TO INTERPRET THE RESULTS")
    print("=" * 70)
    print()
    print("Win Rate: Percentage of profitable trades")
    print("  - Above 50% is good for this type of pattern strategy")
    print()
    print("Profit Factor: Ratio of gross profits to gross losses")
    print("  - Above 1.0 means profitable overall")
    print("  - Above 2.0 is excellent")
    print()
    print("Max Drawdown: Largest peak-to-trough decline")
    print("  - Lower is better")
    print("  - Keep below 20% for acceptable risk")
    print()
    print("Sharpe Ratio: Risk-adjusted returns")
    print("  - Above 1.0 is good")
    print("  - Above 2.0 is excellent")
    print("=" * 70)


if __name__ == "__main__":
    main()
