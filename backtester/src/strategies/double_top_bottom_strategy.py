"""Trading strategy based on double top and double bottom patterns."""

import pandas as pd
from typing import Tuple

from .base_strategy import BaseStrategy
import src.patterns as Patterns


class DoubleTopBottomStrategy(BaseStrategy):
    """
    Strategy that trades double top and double bottom patterns.

    Trading Rules:
    - BUY: When a double bottom pattern is detected (bullish reversal)
    - SELL: When a double top pattern is detected (bearish reversal)

    Pattern Detection Parameters:
    - tolerance: How close the two peaks/troughs must be (default: 2%)
    - min_bars_between: Minimum bars between peaks/troughs (default: 10)
    - max_bars_between: Maximum bars between peaks/troughs (default: 100)
    - peak_order: Sensitivity for peak detection (default: 5)

    Example:
        >>> strategy = DoubleTopBottomStrategy(data, config={
        ...     'tolerance': 0.015,  # 1.5% tolerance
        ...     'min_bars_between': 15,
        ...     'peak_order': 7
        ... })
        >>> results = strategy.backtest()
    """

    def configure(self) -> None:
        """Configure strategy parameters."""
        # Pattern detection parameters
        self.tolerance = self.config.get('tolerance', 0.02)  # 2% default
        self.min_bars_between = self.config.get('min_bars_between', 10)
        self.max_bars_between = self.config.get('max_bars_between', 100)
        self.peak_order = self.config.get('peak_order', 5)
        self.trough_order = self.config.get('trough_order', 5)

        self.logger.info(f"Strategy configured with:")
        self.logger.info(f"  - Tolerance: {self.tolerance * 100}%")
        self.logger.info(f"  - Bars between patterns: {self.min_bars_between} to {self.max_bars_between}")
        self.logger.info(f"  - Peak/Trough order: {self.peak_order}/{self.trough_order}")

    def calculate_indicators(self) -> None:
        """
        Calculate pattern indicators.

        For this strategy, we don't use traditional indicators,
        but rather pattern detection algorithms.
        """
        self.logger.info("Detecting double top patterns...")
        self.patterns['double_top'] = Patterns.detect_double_top(
            self.data,
            peak_column='high',
            peak_order=self.peak_order,
            tolerance=self.tolerance,
            min_bars_between=self.min_bars_between,
            max_bars_between=self.max_bars_between
        )

        double_top_count = self.patterns['double_top']['double_top'].sum()
        self.logger.info(f"Found {double_top_count} double top patterns")

        self.logger.info("Detecting double bottom patterns...")
        self.patterns['double_bottom'] = Patterns.detect_double_bottom(
            self.data,
            trough_column='low',
            trough_order=self.trough_order,
            tolerance=self.tolerance,
            min_bars_between=self.min_bars_between,
            max_bars_between=self.max_bars_between
        )

        double_bottom_count = self.patterns['double_bottom']['double_bottom'].sum()
        self.logger.info(f"Found {double_bottom_count} double bottom patterns")

    def generate_signals(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate trading signals from pattern detection.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]:
                - buy_signals: True when double bottom detected (bullish)
                - sell_signals: True when double top detected (bearish)
        """
        # Buy on double bottom (bullish reversal)
        buy_signals = self.patterns['double_bottom']['double_bottom']

        # Sell on double top (bearish reversal)
        sell_signals = self.patterns['double_top']['double_top']

        buy_count = buy_signals.sum()
        sell_count = sell_signals.sum()

        self.logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")

        return buy_signals, sell_signals


class DoubleBottomOnlyStrategy(BaseStrategy):
    """
    Strategy that only trades double bottom patterns (long only).

    This is a more conservative strategy that only takes long positions
    when double bottom patterns are detected.

    Trading Rules:
    - BUY: When a double bottom is detected
    - SELL: After holding for N bars OR when price drops X%

    Additional Parameters:
    - hold_bars: Number of bars to hold position (default: 20)
    - stop_loss_pct: Stop loss percentage (default: 0.03 = 3%)

    Example:
        >>> strategy = DoubleBottomOnlyStrategy(data, config={
        ...     'tolerance': 0.015,
        ...     'hold_bars': 30,
        ...     'stop_loss_pct': 0.02
        ... })
        >>> results = strategy.backtest()
    """

    def configure(self) -> None:
        """Configure strategy parameters."""
        # Pattern detection
        self.tolerance = self.config.get('tolerance', 0.02)
        self.min_bars_between = self.config.get('min_bars_between', 10)
        self.max_bars_between = self.config.get('max_bars_between', 100)
        self.trough_order = self.config.get('trough_order', 5)

        # Exit rules
        self.hold_bars = self.config.get('hold_bars', 20)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.03)

        self.logger.info(f"Strategy configured:")
        self.logger.info(f"  - Pattern tolerance: {self.tolerance * 100}%")
        self.logger.info(f"  - Hold period: {self.hold_bars} bars")
        self.logger.info(f"  - Stop loss: {self.stop_loss_pct * 100}%")

    def calculate_indicators(self) -> None:
        """Detect double bottom patterns only."""
        self.logger.info("Detecting double bottom patterns...")

        self.patterns['double_bottom'] = Patterns.detect_double_bottom(
            self.data,
            trough_column='low',
            trough_order=self.trough_order,
            tolerance=self.tolerance,
            min_bars_between=self.min_bars_between,
            max_bars_between=self.max_bars_between
        )

        pattern_count = self.patterns['double_bottom']['double_bottom'].sum()
        self.logger.info(f"Found {pattern_count} double bottom patterns")

    def generate_signals(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate buy signals from double bottoms.
        Generate sell signals after hold period.
        """
        # Buy on double bottom
        buy_signals = self.patterns['double_bottom']['double_bottom'].copy()

        # Sell after N bars
        sell_signals = pd.Series(False, index=self.data.index)

        # For each buy signal, create a sell signal N bars later
        buy_indices = buy_signals[buy_signals].index
        for buy_idx in buy_indices:
            idx_pos = self.data.index.get_loc(buy_idx)
            sell_pos = min(idx_pos + self.hold_bars, len(self.data) - 1)
            sell_signals.iloc[sell_pos] = True

        buy_count = buy_signals.sum()
        sell_count = sell_signals.sum()

        self.logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")

        return buy_signals, sell_signals
