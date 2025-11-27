"""Base strategy class for all trading strategies."""

import pandas as pd
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import logging

# Import patterns for pattern recognition strategies
import src.patterns as Patterns
from src.portfolio.base import Portfolio

# Note: src.indicators is imported separately in strategies that need it
# to avoid pandas_ta dependency issues


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    To create a custom strategy:
    1. Inherit from BaseStrategy
    2. Implement calculate_indicators() to compute technical indicators
    3. Implement generate_signals() to define buy/sell logic
    4. Optionally override configure() to set custom parameters

    Example:
        class MyStrategy(BaseStrategy):
            def calculate_indicators(self):
                self.indicators['rsi'] = Indicators.RSI.run(self.data)

            def generate_signals(self):
                rsi = self.indicators['rsi']['rsi']
                buy = rsi < 30
                sell = rsi > 70
                return buy, sell
    """

    def __init__(self, data: pd.DataFrame, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the strategy.

        Parameters:
            data (pd.DataFrame): OHLCV price data with columns ['open', 'high', 'low', 'close', 'volume']
            config (dict, optional): Strategy configuration parameters
        """
        self.data = data
        self.config = config or {}
        self.indicators = {}
        self.patterns = {}
        self.buy_signals = None
        self.sell_signals = None
        self.portfolio = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # Apply custom configuration
        self.configure()

    def configure(self) -> None:
        """
        Override this method to set custom strategy parameters.

        Example:
            def configure(self):
                self.rsi_period = self.config.get('rsi_period', 14)
                self.rsi_oversold = self.config.get('rsi_oversold', 30)
        """
        pass

    @abstractmethod
    def calculate_indicators(self) -> None:
        """
        Calculate technical indicators and store them in self.indicators.

        This method must be implemented by child classes.

        Example:
            def calculate_indicators(self):
                self.indicators['rsi'] = Indicators.RSI.run(
                    self.data,
                    source='close',
                    length=14
                )
                self.indicators['sma_20'] = Indicators.SMA.run(
                    self.data,
                    source='close',
                    window=20
                )
        """
        pass

    @abstractmethod
    def generate_signals(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate buy and sell signals based on indicators.

        This method must be implemented by child classes.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (buy_signals, sell_signals)
                Both are boolean DataFrames where True indicates a signal

        Example:
            def generate_signals(self):
                rsi = self.indicators['rsi']['rsi']
                buy = rsi < 30   # Oversold
                sell = rsi > 70  # Overbought
                return buy, sell
        """
        pass

    def backtest(self) -> pd.DataFrame:
        """
        Run the complete backtest.

        This method:
        1. Calculates indicators
        2. Generates buy/sell signals
        3. Simulates portfolio performance
        4. Returns performance statistics

        Returns:
            pd.DataFrame: Performance statistics including profit, returns, etc.
        """
        self.logger.info(f"Starting backtest for {self.__class__.__name__}")

        # Step 1: Calculate indicators
        self.logger.info("Calculating indicators...")
        self.calculate_indicators()

        # Step 2: Generate signals
        self.logger.info("Generating signals...")
        self.buy_signals, self.sell_signals = self.generate_signals()

        # Validate signals
        if self.buy_signals is None or self.sell_signals is None:
            raise ValueError("generate_signals() must return (buy_signals, sell_signals)")

        # Step 3: Calculate portfolio performance
        self.logger.info("Calculating portfolio performance...")
        self.portfolio = Portfolio.from_signals(self.data, self.buy_signals, self.sell_signals)

        # Step 4: Get statistics
        stats = self.portfolio.get_stats()

        self.logger.info(f"Backtest complete. Results:\n{stats}")

        return stats

    def get_trade_count(self) -> int:
        """
        Count the number of trades executed.

        Returns:
            int: Number of buy signals (trades)
        """
        if self.buy_signals is None:
            return 0

        if isinstance(self.buy_signals, pd.DataFrame):
            return self.buy_signals.sum().sum()
        elif isinstance(self.buy_signals, pd.Series):
            return self.buy_signals.sum()
        else:
            return 0

    def get_signals_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame showing where buy/sell signals occurred.

        Returns:
            pd.DataFrame: DataFrame with columns ['buy', 'sell', 'price']
        """
        if self.buy_signals is None or self.sell_signals is None:
            raise ValueError("Must run backtest() first to generate signals")

        result = pd.DataFrame(index=self.data.index)
        result['buy'] = self.buy_signals
        result['sell'] = self.sell_signals
        result['price'] = self.data['close']

        return result

    def plot_signals(self) -> Dict[str, Any]:
        """
        Prepare data for plotting (for future visualization).

        Returns:
            dict: Dictionary with price data and signal markers
        """
        signals_df = self.get_signals_dataframe()

        return {
            'price': self.data['close'].tolist(),
            'buy_signals': signals_df[signals_df['buy']].index.tolist(),
            'sell_signals': signals_df[signals_df['sell']].index.tolist(),
            'timestamps': self.data.index.tolist()
        }

    def summary(self) -> str:
        """
        Get a text summary of the strategy and its performance.

        Returns:
            str: Formatted summary string
        """
        if self.portfolio is None:
            return f"Strategy: {self.__class__.__name__}\nStatus: Not yet backtested"

        stats = self.portfolio.get_stats()
        trade_count = self.get_trade_count()

        summary = f"""
{'=' * 50}
Strategy: {self.__class__.__name__}
{'=' * 50}
Data Period: {self.data.index[0]} to {self.data.index[-1]}
Total Bars: {len(self.data)}
Number of Trades: {trade_count}

Performance:
{stats.to_string()}
{'=' * 50}
"""
        return summary
