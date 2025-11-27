import pandas as pd
import numpy as np


class Portfolio:
    initial_balance = 1_000
    volume = 1_000

    def __init__(self, data: pd.DataFrame, positions: pd.DataFrame):
        self.data = data
        self.positions = positions
        self.strat_rets = self.calculate_returns(data, positions)
        self.stats = self.calculate_stats()
        self.equity_curve = self.calculate_equity_curve()

    def get_stats(self):
        return self.stats

    def calculate_stats(self) -> pd.DataFrame:
        """Calculate comprehensive portfolio statistics."""
        # Basic profit metrics
        profit_percentage = self.strat_rets.sum() * 100
        profit_money = profit_percentage / 100 * self.volume

        # Trade statistics
        trades = self.count_trades()
        winning_trades = self.count_winning_trades()
        losing_trades = trades - winning_trades
        win_rate = (winning_trades / trades * 100) if trades > 0 else 0

        # Return metrics
        avg_return = self.strat_rets[self.strat_rets != 0].mean() * 100 if trades > 0 else 0

        # Risk metrics
        max_dd = self.calculate_max_drawdown()
        sharpe = self.calculate_sharpe_ratio()

        # Profit factor
        profit_factor = self.calculate_profit_factor()

        # Helper function to extract scalar values
        def to_scalar(value):
            if isinstance(value, pd.Series):
                return value.iloc[0] if len(value) > 0 else 0
            return value

        # Combine all statistics in a DataFrame
        stats = pd.DataFrame({
            'Total Profit (%)': [round(to_scalar(profit_percentage), 2)],
            'Total Profit ($)': [round(to_scalar(profit_money), 2)],
            'Number of Trades': [trades],
            'Winning Trades': [winning_trades],
            'Losing Trades': [losing_trades],
            'Win Rate (%)': [round(to_scalar(win_rate), 2)],
            'Avg Return per Trade (%)': [round(to_scalar(avg_return), 4)],
            'Max Drawdown (%)': [round(max_dd, 2)],
            'Sharpe Ratio': [round(sharpe, 2)],
            'Profit Factor': [round(profit_factor, 2)]
        }, index=['Strategy'])

        return stats

    def count_trades(self) -> int:
        """Count number of trades executed."""
        if isinstance(self.positions, pd.DataFrame):
            position_changes = self.positions.diff()
            trades = (position_changes == 1).sum().sum()
        else:
            position_changes = self.positions.diff()
            trades = (position_changes == 1).sum()
        return int(trades)

    def count_winning_trades(self) -> int:
        """Count number of winning trades."""
        winning = (self.strat_rets > 0).sum()
        return int(winning.sum() if isinstance(winning, pd.Series) else winning)

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage."""
        cumulative_returns = (1 + self.strat_rets).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max

        max_dd = drawdown.min()
        return float(abs(max_dd * 100) if not isinstance(max_dd, (int, float)) else abs(max_dd * 100))

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio (annualized).

        Parameters:
            risk_free_rate: Annual risk-free rate (default: 0.0)

        Returns:
            float: Sharpe ratio
        """
        returns = self.strat_rets[self.strat_rets != 0]

        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate

        if excess_returns.std() == 0:
            return 0.0

        # Annualize assuming daily data (252 trading days)
        sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())

        return float(sharpe if not isinstance(sharpe, pd.Series) else sharpe.iloc[0])

    def calculate_profit_factor(self) -> float:
        """
        Calculate profit factor (gross profit / gross loss).

        Returns:
            float: Profit factor
        """
        winning_returns = self.strat_rets[self.strat_rets > 0].sum()
        losing_returns = abs(self.strat_rets[self.strat_rets < 0].sum())

        if losing_returns == 0:
            return float('inf') if winning_returns > 0 else 0.0

        pf = winning_returns / losing_returns
        return float(pf if not isinstance(pf, pd.Series) else pf.iloc[0])

    def calculate_equity_curve(self) -> pd.DataFrame:
        """
        Calculate equity curve over time.

        Returns:
            pd.DataFrame: Equity curve showing portfolio value over time
        """
        cumulative_returns = (1 + self.strat_rets).cumprod()
        equity = self.initial_balance * cumulative_returns

        return pd.DataFrame({
            'equity': equity,
            'returns': self.strat_rets
        })

    def get_trade_log(self) -> pd.DataFrame:
        """
        Get detailed trade log.

        Returns:
            pd.DataFrame: Log of all trades with entry/exit prices and returns
        """
        trades = []
        position_changes = self.positions.diff()

        # Find entry points (position goes from 0 to 1)
        entries = position_changes == 1

        for idx in self.data.index[entries]:
            idx_pos = self.data.index.get_loc(idx)

            if idx_pos < len(self.data) - 2:
                entry_price = self.data['open'].iloc[idx_pos + 1]
                exit_price = self.data['open'].iloc[idx_pos + 2]
                trade_return = (exit_price - entry_price) / entry_price

                trades.append({
                    'entry_time': idx,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': trade_return,
                    'profit_pct': trade_return * 100,
                    'profit_usd': trade_return * self.volume
                })

        return pd.DataFrame(trades)
    
    @staticmethod
    def calculate_returns(data: pd.DataFrame, positions: pd.DataFrame) -> pd.DataFrame:
        entry_price = data['open'].shift(-1)
        exit_price = data['open'].shift(-2)
        returns = (exit_price - entry_price) / entry_price

        strat_rets = (returns * positions).fillna(0)
        return strat_rets
    
    @staticmethod
    def signals_to_positions(buy_signals, sell_signals):
        """
        Convert buy/sell signals to position indicators.

        Parameters:
            buy_signals: pd.Series or pd.DataFrame with boolean buy signals
            sell_signals: pd.Series or pd.DataFrame with boolean sell signals

        Returns:
            pd.Series or pd.DataFrame with boolean position indicators (True = in position)
        """
        # Handle Series input (convert to numpy for consistency)
        is_series = isinstance(buy_signals, pd.Series)

        signals = np.where(buy_signals, 1,
                        np.where(sell_signals, -1, np.nan))

        if is_series:
            # Create a Series for single-column data
            ffill_signals = pd.Series(signals, index=buy_signals.index)
            ffill_signals = ffill_signals.ffill().fillna(-1).astype(int)
            positions = (ffill_signals + 1) // 2
            return positions.astype(np.bool_)
        else:
            # Create a DataFrame for multi-column data
            ffill_signals = pd.DataFrame(signals, columns=buy_signals.columns, index=buy_signals.index)
            ffill_signals = ffill_signals.ffill().fillna(-1).astype(int)
            positions = (ffill_signals + 1) // 2
            return positions.astype(np.bool_)

    @classmethod
    def from_signals(cls, data: pd.DataFrame, buy_signals: pd.DataFrame, sell_signals: pd.DataFrame) -> pd.DataFrame:
        positions = cls.signals_to_positions(buy_signals, sell_signals)

        return cls(data, positions)
    