"""Peak and trough detection for pattern recognition."""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema


def find_peaks(data: pd.DataFrame, column: str = 'high', order: int = 5) -> pd.DataFrame:
    """
    Find local peaks (tops) in price data.

    A peak is a point where the value is higher than 'order' points on both sides.

    Parameters:
        data (pd.DataFrame): Price data with OHLCV columns
        column (str): Column to analyze (default: 'high')
        order (int): How many points on each side to use for comparison (default: 5)

    Returns:
        pd.DataFrame: Boolean DataFrame where True indicates a peak

    Example:
        >>> peaks = find_peaks(data, column='high', order=5)
        >>> # Returns True where local maxima exist
    """
    result = pd.DataFrame(False, index=data.index, columns=['peak'])

    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")

    # Find local maxima using scipy
    prices = data[column].values
    peak_indices = argrelextrema(prices, np.greater, order=order)[0]

    # Mark peaks in result DataFrame
    result.iloc[peak_indices] = True

    return result


def find_troughs(data: pd.DataFrame, column: str = 'low', order: int = 5) -> pd.DataFrame:
    """
    Find local troughs (bottoms) in price data.

    A trough is a point where the value is lower than 'order' points on both sides.

    Parameters:
        data (pd.DataFrame): Price data with OHLCV columns
        column (str): Column to analyze (default: 'low')
        order (int): How many points on each side to use for comparison (default: 5)

    Returns:
        pd.DataFrame: Boolean DataFrame where True indicates a trough

    Example:
        >>> troughs = find_troughs(data, column='low', order=5)
        >>> # Returns True where local minima exist
    """
    result = pd.DataFrame(False, index=data.index, columns=['trough'])

    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")

    # Find local minima using scipy
    prices = data[column].values
    trough_indices = argrelextrema(prices, np.less, order=order)[0]

    # Mark troughs in result DataFrame
    result.iloc[trough_indices] = True

    return result


def find_peaks_simple(data: pd.DataFrame, column: str = 'high', window: int = 5) -> pd.DataFrame:
    """
    Simple peak detection using rolling window (alternative method).

    A peak is identified when the value is the highest in the rolling window.

    Parameters:
        data (pd.DataFrame): Price data
        column (str): Column to analyze
        window (int): Size of rolling window

    Returns:
        pd.DataFrame: Boolean DataFrame indicating peaks
    """
    result = pd.DataFrame(False, index=data.index, columns=['peak'])

    prices = data[column]

    # Check if current value is max in rolling window centered on current point
    for i in range(window, len(data) - window):
        window_data = prices.iloc[i - window:i + window + 1]
        if prices.iloc[i] == window_data.max():
            result.iloc[i] = True

    return result


def find_troughs_simple(data: pd.DataFrame, column: str = 'low', window: int = 5) -> pd.DataFrame:
    """
    Simple trough detection using rolling window (alternative method).

    A trough is identified when the value is the lowest in the rolling window.

    Parameters:
        data (pd.DataFrame): Price data
        column (str): Column to analyze
        window (int): Size of rolling window

    Returns:
        pd.DataFrame: Boolean DataFrame indicating troughs
    """
    result = pd.DataFrame(False, index=data.index, columns=['trough'])

    prices = data[column]

    # Check if current value is min in rolling window centered on current point
    for i in range(window, len(data) - window):
        window_data = prices.iloc[i - window:i + window + 1]
        if prices.iloc[i] == window_data.min():
            result.iloc[i] = True

    return result
