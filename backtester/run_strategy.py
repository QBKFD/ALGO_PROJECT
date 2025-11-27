"""
Strategy Runner - Run and backtest trading strategies

This script demonstrates how to use the backtester framework to run pattern recognition strategies.

Usage:
    python run_strategy.py

You can modify this script to:
- Change strategy parameters
- Test different symbols
- Adjust timeframes
- Export results
"""

import logging
import sys
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import strategy and data modules
import src.data as Data
from src.strategies.double_top_bottom_strategy import (
    DoubleTopBottomStrategy,
    DoubleBottomOnlyStrategy
)


def run_double_top_bottom_strategy():
    """
    Run the double top/bottom pattern recognition strategy.

    This strategy:
    - Buys on double bottom patterns (bullish reversal)
    - Sells on double top patterns (bearish reversal)
    """
    logger.info("=" * 60)
    logger.info("Running Double Top/Bottom Pattern Strategy")
    logger.info("=" * 60)

    # 1. Load historical data
    logger.info("Loading historical data...")

    # Example: Get data for symbol_id 1 (you would replace with your actual symbol)
    # Timeframe: 60 = 1 hour bars
    symbol_id = 1
    timeframe = 60

    try:
        # Fetch data from database
        data = Data.get_candles('db', [symbol_id], timeframe=timeframe)
        data = Data.get(data)

        logger.info(f"Loaded {len(data)} bars of data")
        logger.info(f"Date range: {data.index[0]} to {data.index[-1]}")

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        logger.error("Make sure the database API is running and accessible")
        return None

    # 2. Configure strategy parameters
    config = {
        'tolerance': 0.02,          # 2% tolerance for pattern matching
        'min_bars_between': 10,     # Minimum 10 bars between peaks/troughs
        'max_bars_between': 100,    # Maximum 100 bars between peaks/troughs
        'peak_order': 5,            # Peak detection sensitivity
        'trough_order': 5           # Trough detection sensitivity
    }

    # 3. Create and run strategy
    logger.info("Initializing strategy...")
    strategy = DoubleTopBottomStrategy(data, config=config)

    logger.info("Running backtest...")
    results = strategy.backtest()

    # 4. Display results
    logger.info("\n" + "=" * 60)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 60)
    print(results.to_string())
    logger.info("=" * 60)

    # 5. Print detailed summary
    print("\n" + strategy.summary())

    # 6. Get trade log
    if strategy.portfolio:
        trade_log = strategy.portfolio.get_trade_log()
        if len(trade_log) > 0:
            logger.info("\n" + "=" * 60)
            logger.info("TRADE LOG (First 10 trades)")
            logger.info("=" * 60)
            print(trade_log.head(10).to_string())
        else:
            logger.warning("No trades were executed")

    return strategy


def run_double_bottom_only_strategy():
    """
    Run the double bottom only strategy (long-only).

    This strategy:
    - Only buys on double bottom patterns
    - Holds for a fixed number of bars
    """
    logger.info("=" * 60)
    logger.info("Running Double Bottom Only Strategy (Long-Only)")
    logger.info("=" * 60)

    # 1. Load data
    logger.info("Loading historical data...")
    symbol_id = 1
    timeframe = 60

    try:
        data = Data.get_candles('db', [symbol_id], timeframe=timeframe)
        data = Data.get(data)
        logger.info(f"Loaded {len(data)} bars")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return None

    # 2. Configure strategy
    config = {
        'tolerance': 0.015,         # 1.5% tolerance (tighter)
        'min_bars_between': 15,     # Minimum 15 bars between troughs
        'max_bars_between': 80,     # Maximum 80 bars
        'trough_order': 7,          # Higher sensitivity for trough detection
        'hold_bars': 25,            # Hold for 25 bars
        'stop_loss_pct': 0.02       # 2% stop loss
    }

    # 3. Run strategy
    strategy = DoubleBottomOnlyStrategy(data, config=config)
    results = strategy.backtest()

    # 4. Display results
    logger.info("\n" + "=" * 60)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 60)
    print(results.to_string())
    logger.info("=" * 60)

    print("\n" + strategy.summary())

    return strategy


def run_custom_strategy():
    """
    Template for running a custom strategy.

    Copy and modify this function to test your own strategies.
    """
    logger.info("Running custom strategy...")

    # Load your data
    data = Data.get_candles('db', [1], timeframe=60)
    data = Data.get(data)

    # Configure your strategy
    config = {
        # Add your custom parameters here
    }

    # Create your strategy instance
    # strategy = YourCustomStrategy(data, config=config)

    # Run backtest
    # results = strategy.backtest()
    # print(results)

    pass


def main():
    """Main entry point."""
    logger.info("\n" + "=" * 60)
    logger.info("BACKTESTER - Pattern Recognition Strategy Runner")
    logger.info("=" * 60 + "\n")

    # Run different strategies
    try:
        # Strategy 1: Double Top/Bottom
        logger.info("\n### Strategy 1: Double Top/Bottom Pattern ###\n")
        strategy1 = run_double_top_bottom_strategy()

        # Strategy 2: Double Bottom Only
        logger.info("\n\n### Strategy 2: Double Bottom Only (Long-Only) ###\n")
        strategy2 = run_double_bottom_only_strategy()

        logger.info("\n" + "=" * 60)
        logger.info("All backtests completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running strategies: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
