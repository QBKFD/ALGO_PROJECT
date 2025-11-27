# Pattern Recognition Trading Strategy Guide

## Overview

The backtester now includes a complete pattern recognition framework for identifying and trading chart patterns like double tops and double bottoms.

## What Was Built

### 1. Pattern Recognition Module (`src/patterns/`)

Identifies chart patterns automatically:

- **Double Top** - Bearish reversal pattern (SELL signal)
- **Double Bottom** - Bullish reversal pattern (BUY signal)

Features:
- Automatic peak and trough detection
- Pattern confirmation (waits for breakout)
- Configurable tolerance and sensitivity
- Uses scipy for robust peak detection

### 2. Strategy Framework (`src/strategies/`)

A flexible system for creating trading strategies:

- **BaseStrategy** - Abstract base class for all strategies
- **DoubleTopBottomStrategy** - Trades both patterns
- **DoubleBottomOnlyStrategy** - Long-only pattern trading

### 3. Enhanced Portfolio Metrics

Comprehensive performance analysis:

- **Total Profit** - Overall returns in % and $
- **Win Rate** - Percentage of profitable trades
- **Sharpe Ratio** - Risk-adjusted returns
- **Max Drawdown** - Largest peak-to-trough decline
- **Profit Factor** - Gross profit / gross loss ratio
- **Trade Log** - Detailed record of all trades

---

## How Double Top/Bottom Patterns Work

### Double Top Pattern (Bearish)

```
   Peak1              Peak2
    /\                /\
   /  \              /  \
  /    \____Trough___/    \___SELL (breakout down)
```

**Trading Logic:**
1. Price makes a high (Peak 1)
2. Price pulls back to a trough
3. Price rallies back to similar high (Peak 2)
4. **SELL when price breaks below the trough** (confirms pattern)

### Double Bottom Pattern (Bullish)

```
        ___BUY (breakout up)
       /
  ____/    \___Peak___/    \
  \  /              \  /
   \/                \/
Trough1            Trough2
```

**Trading Logic:**
1. Price makes a low (Trough 1)
2. Price bounces to a peak
3. Price declines back to similar low (Trough 2)
4. **BUY when price breaks above the peak** (confirms pattern)

---

## How to Use

### Quick Start - Run the Example

```bash
cd backtester
python example_strategy.py
```

This runs a demo with synthetic data that contains embedded patterns.

**Sample Output:**
```
Found 2 double top patterns
Found 8 double bottom patterns
Generated 8 buy signals and 2 sell signals

BACKTEST RESULTS:
Total Profit (%): 11.04
Win Rate (%): 66.67
Sharpe Ratio: 1.03
Max Drawdown (%): 10.88
Profit Factor: 1.17
```

---

## Creating Your Own Strategy

### Step 1: Create a Strategy File

```python
# backtester/my_custom_strategy.py

from src.strategies.base_strategy import BaseStrategy
import src.patterns as Patterns

class MyPatternStrategy(BaseStrategy):
    """My custom pattern recognition strategy."""

    def configure(self):
        # Set your parameters
        self.tolerance = self.config.get('tolerance', 0.02)  # 2%
        self.min_bars = self.config.get('min_bars_between', 10)
        self.max_bars = self.config.get('max_bars_between', 100)

    def calculate_indicators(self):
        # Detect patterns
        self.patterns['double_bottom'] = Patterns.detect_double_bottom(
            self.data,
            tolerance=self.tolerance,
            min_bars_between=self.min_bars,
            max_bars_between=self.max_bars
        )

    def generate_signals(self):
        # Buy on double bottom
        buy = self.patterns['double_bottom']['double_bottom']
        # Sell after 20 bars (example)
        sell = buy.shift(20).fillna(False)

        return buy, sell
```

### Step 2: Load Data and Run

```python
import src.data as Data

# Load historical data from database
data = Data.get_candles('db', [symbol_id], timeframe=60)
data = Data.get(data)

# Configure strategy
config = {
    'tolerance': 0.015,      # 1.5% pattern matching tolerance
    'min_bars_between': 15,  # Minimum 15 bars between troughs
    'max_bars_between': 80   # Maximum 80 bars between troughs
}

# Run backtest
from my_custom_strategy import MyPatternStrategy
strategy = MyPatternStrategy(data, config=config)
results = strategy.backtest()

print(results)
print(strategy.summary())
```

---

## Strategy Parameters Explained

### Pattern Detection Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tolerance` | 0.02 | How close peaks/troughs must be (2% = ±2%) |
| `min_bars_between` | 10 | Minimum bars between peaks/troughs |
| `max_bars_between` | 100 | Maximum bars between peaks/troughs |
| `peak_order` | 5 | Sensitivity for peak detection (higher = stricter) |
| `trough_order` | 5 | Sensitivity for trough detection |

**Examples:**

```python
# Tight patterns (short-term trading)
config = {
    'tolerance': 0.01,       # Very similar highs/lows (1%)
    'min_bars_between': 5,   # Patterns form quickly
    'max_bars_between': 30,  # Patterns resolve quickly
    'peak_order': 3          # More sensitive
}

# Loose patterns (swing trading)
config = {
    'tolerance': 0.03,       # More flexibility (3%)
    'min_bars_between': 20,  # Patterns take time to form
    'max_bars_between': 150, # Patterns can be wide
    'peak_order': 7          # Stricter peak detection
}
```

---

## Understanding the Results

### Performance Metrics

**Total Profit (%)**: Overall return
- Positive = profitable
- Negative = loss

**Win Rate (%)**: Percentage of winning trades
- Above 50% = more winners than losers
- 60%+ is very good for pattern strategies

**Sharpe Ratio**: Risk-adjusted return
- Above 1.0 = good
- Above 2.0 = excellent
- Below 0.5 = poor risk/reward

**Max Drawdown (%)**: Worst peak-to-trough decline
- Below 10% = conservative
- 10-20% = moderate risk
- Above 20% = high risk

**Profit Factor**: Gross profit ÷ Gross loss
- Above 1.0 = profitable overall
- Above 1.5 = good
- Above 2.0 = excellent

---

## Advanced Usage

### Get Detailed Trade Log

```python
strategy = DoubleTopBottomStrategy(data, config=config)
strategy.backtest()

# Get individual trades
trade_log = strategy.portfolio.get_trade_log()
print(trade_log)

# Output:
#   entry_time         entry_price  exit_price  return  profit_pct  profit_usd
# 0 2024-01-04 00:00   96.38       97.09       0.0074  0.74        7.38
# 1 2024-01-05 04:00   93.51       92.63      -0.0095 -0.95       -9.47
```

### Get Equity Curve

```python
equity = strategy.portfolio.equity_curve
print(equity)

# Plot it (requires matplotlib)
import matplotlib.pyplot as plt
plt.plot(equity['equity'])
plt.title('Strategy Equity Curve')
plt.xlabel('Time')
plt.ylabel('Portfolio Value ($)')
plt.show()
```

### Get Signal Timestamps

```python
signals = strategy.get_signals_dataframe()
buy_times = signals[signals['buy']].index.tolist()
sell_times = signals[signals['sell']].index.tolist()

print(f"Buy signals at: {buy_times}")
print(f"Sell signals at: {sell_times}")
```

---

## Common Patterns to Try

### 1. Conservative Pattern Trading

```python
config = {
    'tolerance': 0.01,       # Very strict pattern matching
    'min_bars_between': 20,  # Only wide patterns
    'max_bars_between': 100,
    'peak_order': 7          # Very strict peak detection
}
```

**Good for:** High win rate, fewer trades

### 2. Aggressive Pattern Trading

```python
config = {
    'tolerance': 0.03,      # Loose pattern matching
    'min_bars_between': 5,  # Quick patterns
    'max_bars_between': 50,
    'peak_order': 3         # Sensitive detection
}
```

**Good for:** More trades, lower win rate

### 3. Swing Trading

```python
config = {
    'tolerance': 0.025,
    'min_bars_between': 30,  # Long-term patterns
    'max_bars_between': 200,
    'peak_order': 5
}
```

**Good for:** Longer-term position holding

---

## Integration with Your Repository

### Option 1: Run Standalone

Use `example_strategy.py` for testing with synthetic data.

### Option 2: Connect to Your Database

Modify `run_strategy.py` to:
1. Connect to your PostgreSQL database
2. Fetch real OHLCV data
3. Run strategies on actual market data

**Prerequisites:**
- Database API must be running on `http://database-accessor-api:8000`
- Or modify `src/data/feeds/databaseAccessor.py` to use your backend's API

### Option 3: Create Custom Strategies

1. Create new strategy file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `calculate_indicators()` and `generate_signals()`
4. Run with your data

---

## Next Steps

### 1. Add More Patterns

You can extend `src/patterns/` to detect:
- Head and shoulders
- Triangles
- Flags and pennants
- Cup and handle

### 2. Add More Indicators

Combine patterns with indicators:

```python
def calculate_indicators(self):
    # Detect pattern
    self.patterns['double_bottom'] = Patterns.detect_double_bottom(...)

    # Add RSI filter (requires fixing pandas_ta)
    # self.indicators['rsi'] = Indicators.RSI.run(self.data)

def generate_signals(self):
    pattern = self.patterns['double_bottom']['double_bottom']
    # rsi_oversold = self.indicators['rsi']['rsi'] < 30

    # Buy only when pattern AND RSI oversold
    # buy = pattern & rsi_oversold

    buy = pattern
    sell = ...  # Your sell logic
    return buy, sell
```

### 3. Add Risk Management

Implement stop-loss and take-profit:

```python
def generate_signals(self):
    buy = self.patterns['double_bottom']['double_bottom']

    # Calculate stop-loss levels
    entry_prices = self.data.loc[buy, 'close']
    stop_levels = entry_prices * 0.98  # 2% stop-loss

    # Exit when price hits stop
    sell = self.data['close'] < stop_levels.reindex(self.data.index).ffill()

    return buy, sell
```

---

## File Structure

```
backtester/
├── example_strategy.py          # Standalone demo
├── run_strategy.py              # Production runner
├── src/
│   ├── patterns/                # Pattern recognition
│   │   ├── peaks.py            # Peak/trough detection
│   │   └── double_patterns.py  # Double top/bottom
│   ├── strategies/              # Strategy framework
│   │   ├── base_strategy.py    # Base class
│   │   └── double_top_bottom_strategy.py
│   └── portfolio/               # Performance calculation
│       └── base.py             # Enhanced metrics
```

---

## Troubleshooting

### "No patterns detected"

- Try increasing `tolerance` (e.g., 0.03)
- Decrease `peak_order` / `trough_order` (e.g., 3)
- Adjust `min_bars_between` and `max_bars_between`

### "Too many false signals"

- Decrease `tolerance` (e.g., 0.01)
- Increase `peak_order` / `trough_order` (e.g., 7)
- Increase `min_bars_between`

### "No trades executed"

- Check that patterns are being detected (check logs)
- Verify buy/sell signal generation logic
- Ensure data has enough bars

---

## Support

For questions or issues:
1. Check the example scripts
2. Review the docstrings in the code
3. Adjust parameters and re-run

**Happy Trading! 📈**
