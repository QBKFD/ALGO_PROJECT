"""Double top and double bottom pattern detection."""

import pandas as pd
import numpy as np
from .peaks import find_peaks, find_troughs


def detect_double_top(
    data: pd.DataFrame,
    peak_column: str = 'high',
    peak_order: int = 5,
    tolerance: float = 0.02,
    min_bars_between: int = 10,
    max_bars_between: int = 100
) -> pd.DataFrame:
    """
    Detect double top chart pattern.

    A double top consists of two peaks at approximately the same price level,
    separated by a trough. This is a bearish reversal pattern.

    Pattern structure:
        Peak1 (high) -> Trough (pullback) -> Peak2 (similar high) -> Breakdown (SELL signal)

    Parameters:
        data (pd.DataFrame): OHLCV price data
        peak_column (str): Column to use for peak detection (default: 'high')
        peak_order (int): Sensitivity for peak detection (default: 5)
        tolerance (float): How close the two peaks must be (default: 0.02 = 2%)
        min_bars_between (int): Minimum bars between peaks (default: 10)
        max_bars_between (int): Maximum bars between peaks (default: 100)

    Returns:
        pd.DataFrame: Boolean Series where True indicates a double top pattern was confirmed

    Trading Logic:
        - When double top is detected → SELL signal (bearish reversal)
        - Entry: After price breaks below the trough between the two peaks
        - Stop: Above the second peak
        - Target: Distance from peak to trough, projected downward

    Example:
        >>> double_tops = detect_double_top(data, tolerance=0.015)
        >>> # True values indicate confirmed double top pattern
    """
    result = pd.DataFrame(False, index=data.index, columns=['double_top'])

    # Find all peaks
    peaks = find_peaks(data, column=peak_column, order=peak_order)
    peak_indices = peaks[peaks['peak']].index.tolist()

    if len(peak_indices) < 2:
        return result

    # Check each consecutive pair of peaks
    for i in range(len(peak_indices) - 1):
        for j in range(i + 1, len(peak_indices)):
            idx1 = data.index.get_loc(peak_indices[i])
            idx2 = data.index.get_loc(peak_indices[j])

            bars_between = idx2 - idx1

            # Check distance constraint
            if bars_between < min_bars_between or bars_between > max_bars_between:
                continue

            # Get peak prices
            price1 = data[peak_column].iloc[idx1]
            price2 = data[peak_column].iloc[idx2]

            # Check if peaks are at similar level (within tolerance)
            price_diff = abs(price2 - price1) / price1
            if price_diff > tolerance:
                continue

            # Find the trough between the two peaks
            trough_region = data.iloc[idx1:idx2]
            if len(trough_region) == 0:
                continue

            trough_price = trough_region['low'].min()
            trough_idx_relative = trough_region['low'].idxmin()
            trough_idx = data.index.get_loc(trough_idx_relative)

            # Check for confirmation: price breaks below the trough
            # Look ahead a few bars after the second peak
            lookforward = min(10, len(data) - idx2 - 1)
            if lookforward > 0:
                future_prices = data['close'].iloc[idx2:idx2 + lookforward]
                if any(future_prices < trough_price):
                    # Pattern confirmed - find first break below trough
                    breaks_below = future_prices < trough_price
                    first_break_relative = breaks_below[breaks_below].index[0]
                    confirmation_idx = data.index.get_loc(first_break_relative)
                    if confirmation_idx < len(result):
                        result.iloc[confirmation_idx] = True
                    break  # Found a pattern, move to next peak

    return result


def detect_double_bottom(
    data: pd.DataFrame,
    trough_column: str = 'low',
    trough_order: int = 5,
    tolerance: float = 0.02,
    min_bars_between: int = 10,
    max_bars_between: int = 100
) -> pd.DataFrame:
    """
    Detect double bottom chart pattern.

    A double bottom consists of two troughs at approximately the same price level,
    separated by a peak. This is a bullish reversal pattern.

    Pattern structure:
        Trough1 (low) -> Peak (bounce) -> Trough2 (similar low) -> Breakout (BUY signal)

    Parameters:
        data (pd.DataFrame): OHLCV price data
        trough_column (str): Column to use for trough detection (default: 'low')
        trough_order (int): Sensitivity for trough detection (default: 5)
        tolerance (float): How close the two troughs must be (default: 0.02 = 2%)
        min_bars_between (int): Minimum bars between troughs (default: 10)
        max_bars_between (int): Maximum bars between troughs (default: 100)

    Returns:
        pd.DataFrame: Boolean Series where True indicates a double bottom pattern was confirmed

    Trading Logic:
        - When double bottom is detected → BUY signal (bullish reversal)
        - Entry: After price breaks above the peak between the two troughs
        - Stop: Below the second trough
        - Target: Distance from trough to peak, projected upward

    Example:
        >>> double_bottoms = detect_double_bottom(data, tolerance=0.015)
        >>> # True values indicate confirmed double bottom pattern
    """
    result = pd.DataFrame(False, index=data.index, columns=['double_bottom'])

    # Find all troughs
    troughs = find_troughs(data, column=trough_column, order=trough_order)
    trough_indices = troughs[troughs['trough']].index.tolist()

    if len(trough_indices) < 2:
        return result

    # Check each consecutive pair of troughs
    for i in range(len(trough_indices) - 1):
        for j in range(i + 1, len(trough_indices)):
            idx1 = data.index.get_loc(trough_indices[i])
            idx2 = data.index.get_loc(trough_indices[j])

            bars_between = idx2 - idx1

            # Check distance constraint
            if bars_between < min_bars_between or bars_between > max_bars_between:
                continue

            # Get trough prices
            price1 = data[trough_column].iloc[idx1]
            price2 = data[trough_column].iloc[idx2]

            # Check if troughs are at similar level (within tolerance)
            price_diff = abs(price2 - price1) / price1
            if price_diff > tolerance:
                continue

            # Find the peak between the two troughs
            peak_region = data.iloc[idx1:idx2]
            if len(peak_region) == 0:
                continue

            peak_price = peak_region['high'].max()
            peak_idx_relative = peak_region['high'].idxmax()
            peak_idx = data.index.get_loc(peak_idx_relative)

            # Check for confirmation: price breaks above the peak
            # Look ahead a few bars after the second trough
            lookforward = min(10, len(data) - idx2 - 1)
            if lookforward > 0:
                future_prices = data['close'].iloc[idx2:idx2 + lookforward]
                if any(future_prices > peak_price):
                    # Pattern confirmed - find first break above peak
                    breaks_above = future_prices > peak_price
                    first_break_relative = breaks_above[breaks_above].index[0]
                    confirmation_idx = data.index.get_loc(first_break_relative)
                    if confirmation_idx < len(result):
                        result.iloc[confirmation_idx] = True
                    break  # Found a pattern, move to next trough

    return result


def detect_head_and_shoulders(
    data: pd.DataFrame,
    peak_order: int = 5,
    tolerance: float = 0.02
) -> pd.DataFrame:
    """
    Detect head and shoulders pattern (future enhancement).

    This is a placeholder for more advanced pattern recognition.

    Pattern: Left Shoulder -> Head (higher peak) -> Right Shoulder -> Neckline break

    Parameters:
        data (pd.DataFrame): OHLCV data
        peak_order (int): Peak detection sensitivity
        tolerance (float): How similar shoulders should be

    Returns:
        pd.DataFrame: Boolean indicating pattern detection
    """
    result = pd.DataFrame(False, index=data.index, columns=['head_shoulders'])

    # TODO: Implement head and shoulders detection
    # This would require finding 3 peaks where middle is highest
    # and left/right shoulders are at similar levels

    return result
