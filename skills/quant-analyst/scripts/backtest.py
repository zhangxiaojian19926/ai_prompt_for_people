#!/usr/bin/env python3
"""
回测系统 - backtest.py

用途：策略回测引擎，支持多种策略的历史回测

功能：
    - 事件驱动回测
    - 收益率计算
    - 夏普比率
    - 最大回撤
    - 胜率/盈亏比
    - 交易记录
    - 收益曲线

使用示例：
    from backtest import Backtester
    
    bt = Backtester(
        symbol="159928",
        start_date="2023-01-01",
        end_date="2025-12-31"
    )
    
    # 使用均线策略
    result = bt.run_ma_cross_strategy()
    print(bt.generate_report())

依赖：
    pip install pandas numpy matplotlib
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from config import get_config
except ImportError:
    # Fallback for running script standalone without skill structure
    def get_config(section=None):
        configs = {
            "backtest": {"initial_capital": 100000, "risk_free_rate": 0.03, "warmup_period": 60},
            "trading_costs": {"commission": 0.0003, "slippage": 0.001, "stamp_duty": 0.001},
            "ma": {"short": 5, "long": 20},
            "rsi": {"period": 14, "oversold": 30, "overbought": 70},
            "value_strategy": {"buy_threshold": 20, "sell_threshold": 70}
        }
        if section: return configs.get(section, {})
        return configs

try:
    from data_fetcher import DataFetcher
except ImportError:
    DataFetcher = None
try:
    from indicators import TechnicalIndicators
except ImportError:
    TechnicalIndicators = None
try:
    from valuation_data import ValuationDataManager
except ImportError:
    ValuationDataManager = None


class Signal(Enum):
    BUY, SELL, HOLD = "买入", "卖出", "持有"

@dataclass
class Trade:
    date: str; signal: Signal; price: float; shares: int; value: float; reason: str

@dataclass
class BacktestResult:
    total_return: float; annual_return: float; sharpe_ratio: float; max_drawdown: float
    win_rate: float; profit_loss_ratio: float; total_trades: int; winning_trades: int
    losing_trades: int; final_value: float; initial_capital: float
    trades: List[Trade]; equity_curve: pd.DataFrame


class Backtester:
    """ 回测引擎 """
    
    def __init__(self, symbol: str, start_date: str, end_date: str):
        self.backtest_config = get_config("backtest")
        self.trading_costs_config = get_config("trading_costs")
        self.ma_config = get_config("ma")
        self.rsi_config = get_config("rsi")
        self.value_strategy_config = get_config("value_strategy")
        self.position_config = get_config("position")
        
        self.symbol, self.start_date, self.end_date = symbol, start_date, end_date
        self.initial_capital = self.backtest_config.get("initial_capital", 100000)
        self.commission = self.trading_costs_config.get("commission", 0.0003)
        self.slippage = self.trading_costs_config.get("slippage", 0.001)
        self.stamp_duty = self.trading_costs_config.get("stamp_duty", 0.001)
        self.risk_free_rate = self.backtest_config.get("risk_free_rate", 0.03)
        self.warmup_period = self.backtest_config.get("warmup_period", 60)
        
        self.data: Optional[pd.DataFrame] = None
        self.trades: List[Trade] = []
        self.equity_curve: Optional[pd.DataFrame] = None
        self.result: Optional[BacktestResult] = None
        
        self._load_data()
        self._calculate_indicators()

    def _load_data(self):
        if DataFetcher and self.data is None:
            self.data = DataFetcher().get_history_kline(self.symbol, self.start_date, self.end_date)
        elif self.data is None:
            dates = pd.date_range(self.start_date, self.end_date); prices = 1.0 * np.cumprod(1 + np.random.randn(len(dates)) * 0.02)
            self.data = pd.DataFrame({
                'date': dates,
                'open': prices * 0.99,
                'high': prices * 1.02,
                'low': prices * 0.98,
                'close': prices,
                'volume': np.random.randint(1000000, 5000000, len(dates))
            })

    def _calculate_indicators(self):
        if self.data is not None and 'ma5' not in self.data.columns and TechnicalIndicators:
            self.data = TechnicalIndicators(self.data).add_all_indicators()

    @staticmethod
    def _calculate_expanding_percentile(series: pd.Series) -> pd.Series:
        ranks = series.expanding().rank()
        counts = series.expanding().count()
        return ((ranks - 1) / (counts - 1) * 100).fillna(50)

    def _execute_backtest(self, signal_func: Callable) -> BacktestResult:
        cash, shares, equity, self.trades = self.initial_capital, 0, [], []
        for i, row in self.data.iterrows():
            if i < self.warmup_period: equity.append(cash); continue
            price = row['close']; signal, reason = signal_func(self.data.iloc[:i+1], row)
            if signal == Signal.BUY and cash > 0:
                buy_price = price * (1 + self.slippage); shares_to_buy = int(cash / (buy_price * (1 + self.commission)))
                if shares_to_buy > 0:
                    cost = shares_to_buy * buy_price * (1 + self.commission); cash -= cost; shares += shares_to_buy
                    self.trades.append(Trade(str(row['date']), Signal.BUY, buy_price, shares_to_buy, cost, reason))
            elif signal == Signal.SELL and shares > 0:
                sell_price = price * (1 - self.slippage); revenue = shares * sell_price * (1 - self.commission - self.stamp_duty)
                cash += revenue; self.trades.append(Trade(str(row['date']), Signal.SELL, sell_price, shares, revenue, reason)); shares = 0
            equity.append(cash + shares * price)
        self.equity_curve = pd.DataFrame({'date': self.data['date'], 'equity': equity, 'price': self.data['close']})
        return self._calculate_metrics()

    def _get_target_position_by_percentile(self, percentile: float) -> float:
        if pd.isna(percentile): return 0.5
        if percentile < 25: return self.position_config["percentile_0_25"]["max"]
        if percentile < 40: return self.position_config["percentile_25_40"]["max"]
        if percentile < 60: return self.position_config["percentile_40_60"]["max"]
        if percentile < 75: return self.position_config["percentile_60_75"]["min"]
        return self.position_config["percentile_75_100"]["min"]

    def _execute_rebalancing_backtest(self, positioning_func: Callable) -> BacktestResult:
        cash, shares, equity, self.trades = self.initial_capital, 0, [], []
        for i, row in self.data.iterrows():
            current_equity = cash + shares * row['close']
            if i < self.warmup_period: equity.append(current_equity); continue
            
            target_position = positioning_func(row)
            target_value = current_equity * target_position
            current_value = shares * row['close']
            trade_threshold = 0.01 * current_equity # 1% rebalancing threshold
            
            if target_value - current_value > trade_threshold:
                buy_price = row['close'] * (1 + self.slippage); shares_to_buy = int((target_value - current_value) / buy_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * buy_price * (1 + self.commission)
                    if cost <= cash: cash -= cost; shares += shares_to_buy; self.trades.append(Trade(str(row['date']), Signal.BUY, buy_price, shares_to_buy, cost, f"Rebalance to {target_position*100:.0f}%"))
            elif current_value - target_value > trade_threshold:
                shares_to_sell = int((current_value - target_value) / row['close'])
                if shares_to_sell > 0 and shares > 0:
                    shares_to_sell = min(shares, shares_to_sell)
                    sell_price = row['close'] * (1 - self.slippage); revenue = shares_to_sell * sell_price * (1 - self.commission - self.stamp_duty)
                    cash += revenue; shares -= shares_to_sell; self.trades.append(Trade(str(row['date']), Signal.SELL, sell_price, shares_to_sell, revenue, f"Rebalance to {target_position*100:.0f}%"))
            
            equity.append(cash + shares * row['close'])
        self.equity_curve = pd.DataFrame({'date': self.data['date'], 'equity': equity, 'price': self.data['close']})
        return self._calculate_metrics()

    def _calculate_metrics(self) -> BacktestResult:
        equity = self.equity_curve['equity'].values; total_return = (equity[-1] - equity[0]) / equity[0] * 100
        days = len(equity); annual_return = ((equity[-1] / equity[0]) ** (252 / days) - 1) * 100 if days > 0 else 0
        returns = np.diff(equity) / equity[:-1]
        rf = self.risk_free_rate / 252
        sharpe = (np.mean(returns) - rf) / (np.std(returns) + 1e-10) * np.sqrt(252) if np.std(returns) > 0 else 0
        peak = np.maximum.accumulate(equity); drawdown = (peak - equity) / peak * 100; max_drawdown = np.max(drawdown)
        profits = [(self.trades[i+1].value/self.trades[i+1].shares - self.trades[i].value/self.trades[i].shares) / (self.trades[i].value/self.trades[i].shares) * 100 for i in range(len(self.trades) - 1) if self.trades[i].signal==Signal.BUY and self.trades[i+1].signal==Signal.SELL]
        winning_trades, losing_trades = len([p for p in profits if p > 0]), len([p for p in profits if p <= 0]); total_trades = len(profits)
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        avg_win = np.mean([p for p in profits if p > 0]) if winning_trades > 0 else 0
        avg_loss = abs(np.mean([p for p in profits if p <= 0])) if losing_trades > 0 else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        return BacktestResult(total_return=round(total_return,2), annual_return=round(annual_return,2), sharpe_ratio=round(sharpe,2), max_drawdown=round(max_drawdown,2), win_rate=round(win_rate,2), profit_loss_ratio=round(profit_loss_ratio,2), total_trades=total_trades, winning_trades=winning_trades, losing_trades=losing_trades, final_value=round(equity[-1],2), initial_capital=self.initial_capital, trades=self.trades, equity_curve=self.equity_curve)

    def _prepare_valuation_data(self, index_name: str):
        if 'pe_percentile' in self.data.columns: return
        if ValuationDataManager:
            manager = ValuationDataManager(); pe_df, _ = manager.get_valuation_history(index_name)
            if pe_df is not None and not pe_df.empty:
                pe_col = 'pe' if 'pe' in pe_df.columns else '市盈率'
                pe_df = pe_df[['date', pe_col]].rename(columns={pe_col: 'pe'}); pe_df['date'] = pd.to_datetime(pe_df['date'])
                pe_df['pe_percentile'] = self._calculate_expanding_percentile(pe_df['pe'])
                self.data = pd.merge(self.data, pe_df, on='date', how='left')
            else: self.data['pe_percentile'] = self._calculate_expanding_percentile(self.data['close'])
        else: self.data['pe_percentile'] = self._calculate_expanding_percentile(self.data['close'])
        self.data['pe_percentile'] = self.data['pe_percentile'].ffill()

    def run_ma_cross_strategy(self, short: int = None, long: int = None) -> BacktestResult:
        short, long = short or self.ma_config.get("short", 5), long or self.ma_config.get("long", 20)
        def signal_func(history, row):
            prev=history.iloc[-2]
            if row.get(f'ma{short}') > row.get(f'ma{long}') and prev.get(f'ma{short}') <= prev.get(f'ma{long}'): return Signal.BUY, f"MA{short}上穿MA{long}"
            if row.get(f'ma{short}') < row.get(f'ma{long}') and prev.get(f'ma{short}') >= prev.get(f'ma{long}'): return Signal.SELL, f"MA{short}下穿MA{long}"
            return Signal.HOLD, ""
        return self._execute_backtest(signal_func)

    def run_value_invest_strategy(self, index_name: str = "沪深300", pe_buy: float = None, pe_sell: float = None) -> BacktestResult:
        pe_buy, pe_sell = pe_buy or self.value_strategy_config.get("buy_threshold", 20), pe_sell or self.value_strategy_config.get("sell_threshold", 70)
        self._prepare_valuation_data(index_name)
        def signal_func(history, row):
            p = row.get('pe_percentile')
            if pd.isna(p): return Signal.HOLD, ""
            if p < pe_buy: return Signal.BUY, f"估值低位({p:.1f}%)"
            if p > pe_sell: return Signal.SELL, f"估值高位({p:.1f}%)"
            return Signal.HOLD, ""
        return self._execute_backtest(signal_func)
        
    def run_dynamic_position_strategy(self, index_name: str = "沪深300") -> BacktestResult:
        """ 基于PE百分位进行动态仓位管理的回测 """
        self._prepare_valuation_data(index_name)
        return self._execute_rebalancing_backtest(lambda row: self._get_target_position_by_percentile(row.get('pe_percentile', 50)))

    def run_macd_strategy(self) -> BacktestResult:
        """MACD金叉死叉策略"""
        def signal_func(history, row):
            macd = row.get('macd')
            prev = history.iloc[-2] if len(history) > 1 else row
            prev_macd = prev.get('macd')
            if pd.isna(macd) or pd.isna(prev_macd): return Signal.HOLD, ""
            # MACD金叉: 从负变正
            if prev_macd <= 0 and macd > 0: return Signal.BUY, f"MACD金叉({macd:.4f})"
            # MACD死叉: 从正变负
            if prev_macd >= 0 and macd < 0: return Signal.SELL, f"MACD死叉({macd:.4f})"
            return Signal.HOLD, ""
        return self._execute_backtest(signal_func)

    def run_rsi_strategy(self, oversold: int = None, overbought: int = None) -> BacktestResult:
        """RSI超买超卖策略"""
        oversold = oversold or self.rsi_config.get("oversold", 30)
        overbought = overbought or self.rsi_config.get("overbought", 70)
        def signal_func(history, row):
            rsi = row.get('rsi14')
            if pd.isna(rsi): return Signal.HOLD, ""
            if rsi < oversold: return Signal.BUY, f"RSI超卖({rsi:.1f})"
            if rsi > overbought: return Signal.SELL, f"RSI超买({rsi:.1f})"
            return Signal.HOLD, ""
        return self._execute_backtest(signal_func)

    def run_bollinger_strategy(self) -> BacktestResult:
        """布林带突破策略"""
        def signal_func(history, row):
            close = row.get('close')
            upper = row.get('boll_upper')
            lower = row.get('boll_lower')
            if pd.isna(close) or pd.isna(upper) or pd.isna(lower): return Signal.HOLD, ""
            # 跌破下轨买入
            if close < lower: return Signal.BUY, f"跌破布林下轨"
            # 突破上轨卖出
            if close > upper: return Signal.SELL, f"突破布林上轨"
            return Signal.HOLD, ""
        return self._execute_backtest(signal_func)

    def generate_report(self) -> str:
        if not self.result: return "请先运行回测"
        r = self.result; quality = "优秀" if r.sharpe_ratio > 1 and r.max_drawdown < 30 else "良好" if r.sharpe_ratio > 0.5 and r.max_drawdown < 40 else "需改进"
        return f"""
# 策略回测报告
## 基本信息
| 项目 | 数值 |
|:---|:---|
| 标的代码 | {self.symbol} |
| 回测周期 | {self.start_date} ~ {self.end_date} |
| 初始资金 | ¥{r.initial_capital:,.0f} |
| 最终价值 | ¥{r.final_value:,.0f} |
## 业绩指标
| 指标 | 数值 | 评价 |
|:---|:---|:---|
| **总收益率** | {r.total_return}% | {'🟢' if r.total_return > 0 else '🔴'} |
| **年化收益** | {r.annual_return}% | {'🟢' if r.annual_return > 10 else '🟡' if r.annual_return > 0 else '🔴'} |
| **夏普比率** | {r.sharpe_ratio} | {'🟢' if r.sharpe_ratio > 1 else '🟡' if r.sharpe_ratio > 0 else '🔴'} |
| **最大回撤** | {r.max_drawdown}% | {'🟢' if r.max_drawdown < 20 else '🟡' if r.max_drawdown < 40 else '🔴'} |
| **胜率** | {r.win_rate}% | {'🟢' if r.win_rate > 50 else '🔴'} |
| **盈亏比** | {r.profit_loss_ratio} | {'🟢' if r.profit_loss_ratio > 1.5 else '🟡' if r.profit_loss_ratio > 1 else '🔴'} |
## 交易统计
| 项目 | 数值 |
|:---|:---|
| 总交易次数 | {r.total_trades} |
| 盈利次数 | {r.winning_trades} |
| 亏损次数 | {r.losing_trades} |
## 策略评级
**综合评级**: {quality}
---
*本报告仅供参考，回测结果不代表真实收益*
"""

if __name__ == "__main__":
    import argparse
    from datetime import date, timedelta

    parser = argparse.ArgumentParser(description="运行回测引擎.")
    parser.add_argument("-s", "--symbol", type=str, required=True, help="股票/ETF代码 (例如: 159928)")
    parser.add_argument(
        "-t", "--strategy", type=str, required=True, 
        choices=['ma_cross', 'value', 'dynamic'], 
        help="要运行的策略: 'ma_cross', 'value', 'dynamic'"
    )
    # 默认回测周期为过去一年
    end_date = date.today().strftime("%Y-%m-%d")
    start_date = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    parser.add_argument("--start", type=str, default=start_date, help=f"开始日期 (YYYY-MM-DD), 默认为 {start_date}")
    parser.add_argument("--end", type=str, default=end_date, help=f"结束日期 (YYYY-MM-DD), 默认为 {end_date}")
    parser.add_argument("--index", type=str, default="沪深300", help="估值策略参考的指数, 默认为 沪深300")

    args = parser.parse_args()

    print(f"开始回测...")
    print(f"标的: {args.symbol}, 策略: {args.strategy}, 周期: {args.start} to {args.end}")

    bt = Backtester(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end
    )
    
    result = None
    if args.strategy == 'ma_cross':
        print("\n=== 均线交叉策略 ===")
        result = bt.run_ma_cross_strategy()
    elif args.strategy == 'value':
        print("\n=== 估值策略 (信号驱动) ===")
        result = bt.run_value_invest_strategy(index_name=args.index)
    elif args.strategy == 'dynamic':
        print("\n=== 动态仓位策略 (仓位驱动) ===")
        result = bt.run_dynamic_position_strategy(index_name=args.index)

    if result:
        print(bt.generate_report())
    else:
        print("策略运行失败或未产生结果。")
