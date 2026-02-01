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
        end_date="2025-12-31",
        initial_capital=100000
    )
    
    # 使用均线策略
    result = bt.run_ma_cross_strategy(short=5, long=20)
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
    from data_fetcher import DataFetcher
except ImportError:
    DataFetcher = None


class Signal(Enum):
    """交易信号"""
    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"


@dataclass
class Trade:
    """交易记录"""
    date: str
    signal: Signal
    price: float
    shares: int
    value: float
    reason: str


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float          # 总收益率
    annual_return: float         # 年化收益率
    sharpe_ratio: float          # 夏普比率
    max_drawdown: float          # 最大回撤
    win_rate: float              # 胜率
    profit_loss_ratio: float     # 盈亏比
    total_trades: int            # 总交易次数
    winning_trades: int          # 盈利次数
    losing_trades: int           # 亏损次数
    final_value: float           # 最终价值
    initial_capital: float       # 初始资金
    trades: List[Trade]          # 交易记录
    equity_curve: pd.DataFrame   # 收益曲线


class Backtester:
    """
    回测引擎
    
    支持多种策略回测，计算详细的业绩指标
    """
    
    def __init__(self, symbol: str, start_date: str, end_date: str,
                 initial_capital: float = 100000, commission: float = 0.0003):
        """
        初始化回测器
        
        Args:
            symbol: 股票/ETF代码
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            commission: 手续费率
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        
        self.data = None
        self.trades: List[Trade] = []
        self.equity_curve = None
        self.result: Optional[BacktestResult] = None
        
        self._load_data()
    
    def _load_data(self):
        """加载历史数据"""
        if DataFetcher:
            fetcher = DataFetcher()
            self.data = fetcher.get_history_kline(
                self.symbol, self.start_date, self.end_date
            )
        else:
            # 生成模拟数据用于测试
            dates = pd.date_range(self.start_date, self.end_date)
            np.random.seed(42)
            prices = 1.0 * np.cumprod(1 + np.random.randn(len(dates)) * 0.02)
            self.data = pd.DataFrame({
                'date': dates,
                'open': prices * 0.99,
                'high': prices * 1.02,
                'low': prices * 0.98,
                'close': prices,
                'volume': np.random.randint(1000000, 5000000, len(dates))
            })
    
    def _calculate_indicators(self):
        """计算技术指标"""
        df = self.data.copy()
        
        # 移动平均线
        for period in [5, 10, 20, 60, 120]:
            df[f'ma{period}'] = df['close'].rolling(period).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['dif'] = exp1 - exp2
        df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
        df['macd'] = 2 * (df['dif'] - df['dea'])
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['boll_mid'] = df['close'].rolling(20).mean()
        df['boll_std'] = df['close'].rolling(20).std()
        df['boll_upper'] = df['boll_mid'] + 2 * df['boll_std']
        df['boll_lower'] = df['boll_mid'] - 2 * df['boll_std']
        
        self.data = df
    
    def _execute_backtest(self, signal_func: Callable) -> BacktestResult:
        """
        执行回测
        
        Args:
            signal_func: 信号生成函数，接收当前行数据，返回Signal
        """
        self._calculate_indicators()
        
        cash = self.initial_capital
        shares = 0
        equity = []
        self.trades = []
        
        for i, row in self.data.iterrows():
            if i < 60:  # 跳过预热期
                equity.append(cash)
                continue
            
            price = row['close']
            signal, reason = signal_func(self.data.iloc[:i+1], row)
            
            if signal == Signal.BUY and cash > 0:
                # 全仓买入
                shares_to_buy = int(cash * (1 - self.commission) / price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * price * (1 + self.commission)
                    cash -= cost
                    shares += shares_to_buy
                    self.trades.append(Trade(
                        date=str(row['date']),
                        signal=Signal.BUY,
                        price=price,
                        shares=shares_to_buy,
                        value=cost,
                        reason=reason
                    ))
            
            elif signal == Signal.SELL and shares > 0:
                # 全仓卖出
                revenue = shares * price * (1 - self.commission)
                cash += revenue
                self.trades.append(Trade(
                    date=str(row['date']),
                    signal=Signal.SELL,
                    price=price,
                    shares=shares,
                    value=revenue,
                    reason=reason
                ))
                shares = 0
            
            # 计算当日权益
            equity.append(cash + shares * price)
        
        # 构建收益曲线
        self.equity_curve = pd.DataFrame({
            'date': self.data['date'],
            'equity': equity,
            'price': self.data['close']
        })
        
        # 计算业绩指标
        return self._calculate_metrics()
    
    def _calculate_metrics(self) -> BacktestResult:
        """计算业绩指标"""
        equity = self.equity_curve['equity'].values
        
        # 总收益率
        total_return = (equity[-1] - equity[0]) / equity[0] * 100
        
        # 年化收益率
        days = len(equity)
        annual_return = ((equity[-1] / equity[0]) ** (252 / days) - 1) * 100
        
        # 日收益率
        returns = np.diff(equity) / equity[:-1]
        
        # 夏普比率 (假设无风险利率3%)
        rf = 0.03 / 252
        sharpe = (np.mean(returns) - rf) / (np.std(returns) + 1e-10) * np.sqrt(252)
        
        # 最大回撤
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak * 100
        max_drawdown = np.max(drawdown)
        
        # 交易统计
        profits = []
        for i in range(0, len(self.trades) - 1, 2):
            if i + 1 < len(self.trades):
                buy = self.trades[i]
                sell = self.trades[i + 1]
                profit = (sell.price - buy.price) / buy.price * 100
                profits.append(profit)
        
        winning_trades = len([p for p in profits if p > 0])
        losing_trades = len([p for p in profits if p <= 0])
        total_trades = len(profits)
        
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        avg_win = np.mean([p for p in profits if p > 0]) if winning_trades > 0 else 0
        avg_loss = abs(np.mean([p for p in profits if p <= 0])) if losing_trades > 0 else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        self.result = BacktestResult(
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown=round(max_drawdown, 2),
            win_rate=round(win_rate, 2),
            profit_loss_ratio=round(profit_loss_ratio, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            final_value=round(equity[-1], 2),
            initial_capital=self.initial_capital,
            trades=self.trades,
            equity_curve=self.equity_curve
        )
        
        return self.result
    
    # ============ 内置策略 ============
    
    def run_ma_cross_strategy(self, short: int = 5, long: int = 20) -> BacktestResult:
        """
        均线交叉策略
        
        买入：短期均线上穿长期均线
        卖出：短期均线下穿长期均线
        """
        def signal_func(history: pd.DataFrame, row: pd.Series):
            ma_short = row[f'ma{short}']
            ma_long = row[f'ma{long}']
            prev = history.iloc[-2]
            prev_ma_short = prev[f'ma{short}']
            prev_ma_long = prev[f'ma{long}']
            
            if pd.isna(ma_short) or pd.isna(ma_long):
                return Signal.HOLD, ""
            
            # 金叉
            if prev_ma_short <= prev_ma_long and ma_short > ma_long:
                return Signal.BUY, f"MA{short}上穿MA{long}"
            # 死叉
            elif prev_ma_short >= prev_ma_long and ma_short < ma_long:
                return Signal.SELL, f"MA{short}下穿MA{long}"
            
            return Signal.HOLD, ""
        
        return self._execute_backtest(signal_func)
    
    def run_macd_strategy(self) -> BacktestResult:
        """
        MACD策略
        
        买入：DIF上穿DEA
        卖出：DIF下穿DEA
        """
        def signal_func(history: pd.DataFrame, row: pd.Series):
            dif = row['dif']
            dea = row['dea']
            prev = history.iloc[-2]
            prev_dif = prev['dif']
            prev_dea = prev['dea']
            
            if pd.isna(dif) or pd.isna(dea):
                return Signal.HOLD, ""
            
            # 金叉
            if prev_dif <= prev_dea and dif > dea:
                return Signal.BUY, "MACD金叉"
            # 死叉
            elif prev_dif >= prev_dea and dif < dea:
                return Signal.SELL, "MACD死叉"
            
            return Signal.HOLD, ""
        
        return self._execute_backtest(signal_func)
    
    def run_rsi_strategy(self, oversold: int = 30, overbought: int = 70) -> BacktestResult:
        """
        RSI策略
        
        买入：RSI < 超卖阈值
        卖出：RSI > 超买阈值
        """
        def signal_func(history: pd.DataFrame, row: pd.Series):
            rsi = row['rsi']
            
            if pd.isna(rsi):
                return Signal.HOLD, ""
            
            if rsi < oversold:
                return Signal.BUY, f"RSI超卖({rsi:.1f})"
            elif rsi > overbought:
                return Signal.SELL, f"RSI超买({rsi:.1f})"
            
            return Signal.HOLD, ""
        
        return self._execute_backtest(signal_func)
    
    def run_bollinger_strategy(self) -> BacktestResult:
        """
        布林带策略
        
        买入：价格跌破下轨
        卖出：价格突破上轨
        """
        def signal_func(history: pd.DataFrame, row: pd.Series):
            close = row['close']
            upper = row['boll_upper']
            lower = row['boll_lower']
            
            if pd.isna(upper) or pd.isna(lower):
                return Signal.HOLD, ""
            
            if close < lower:
                return Signal.BUY, "跌破布林下轨"
            elif close > upper:
                return Signal.SELL, "突破布林上轨"
            
            return Signal.HOLD, ""
        
        return self._execute_backtest(signal_func)
    
    def run_value_invest_strategy(self, pe_buy: float = 20, pe_sell: float = 70) -> BacktestResult:
        """
        估值策略（简化版，使用价格模拟PE变化）
        
        买入：估值低于买入阈值
        卖出：估值高于卖出阈值
        """
        def signal_func(history: pd.DataFrame, row: pd.Series):
            # 使用价格相对历史的分位模拟PE分位
            prices = history['close']
            current = row['close']
            percentile = (prices < current).sum() / len(prices) * 100
            
            if percentile < pe_buy:
                return Signal.BUY, f"估值低位({percentile:.1f}%分位)"
            elif percentile > pe_sell:
                return Signal.SELL, f"估值高位({percentile:.1f}%分位)"
            
            return Signal.HOLD, ""
        
        return self._execute_backtest(signal_func)
    
    def generate_report(self) -> str:
        """生成回测报告"""
        if not self.result:
            return "请先运行回测"
        
        r = self.result
        
        # 判断策略质量
        if r.sharpe_ratio > 1 and r.max_drawdown < 30:
            quality = "🟢 优秀"
        elif r.sharpe_ratio > 0.5 and r.max_drawdown < 40:
            quality = "🟡 良好"
        else:
            quality = "🔴 需改进"
        
        report = f"""
# 策略回测报告

## 基本信息

| 项目 | 数值 |
|------|------|
| 标的代码 | {self.symbol} |
| 回测周期 | {self.start_date} ~ {self.end_date} |
| 初始资金 | ¥{self.initial_capital:,.0f} |
| 最终价值 | ¥{r.final_value:,.0f} |

## 业绩指标

| 指标 | 数值 | 评价 |
|------|------|------|
| **总收益率** | {r.total_return}% | {"🟢" if r.total_return > 0 else "🔴"} |
| **年化收益** | {r.annual_return}% | {"🟢" if r.annual_return > 10 else "🟡" if r.annual_return > 0 else "🔴"} |
| **夏普比率** | {r.sharpe_ratio} | {"🟢" if r.sharpe_ratio > 1 else "🟡" if r.sharpe_ratio > 0 else "🔴"} |
| **最大回撤** | {r.max_drawdown}% | {"🟢" if r.max_drawdown < 20 else "🟡" if r.max_drawdown < 40 else "🔴"} |
| **胜率** | {r.win_rate}% | {"🟢" if r.win_rate > 50 else "🔴"} |
| **盈亏比** | {r.profit_loss_ratio} | {"🟢" if r.profit_loss_ratio > 1.5 else "🟡" if r.profit_loss_ratio > 1 else "🔴"} |

## 交易统计

| 项目 | 数值 |
|------|------|
| 总交易次数 | {r.total_trades} |
| 盈利次数 | {r.winning_trades} |
| 亏损次数 | {r.losing_trades} |

## 策略评级

**综合评级**: {quality}

## 大师视角点评

### 巴菲特视角
{"这个策略体现了'安全边际'原则，在低估时买入有助于降低风险。" if r.max_drawdown < 30 else "最大回撤较大，需要更注重安全边际，不要在高估时买入。"}

### Howard Marks视角
{"夏普比率表现不错，说明风险调整后收益可观。" if r.sharpe_ratio > 1 else "需要关注风险控制，考虑周期位置，避免在市场高点重仓。"}

---
*本报告仅供参考，回测结果不代表真实收益*
"""
        return report


if __name__ == "__main__":
    # 测试回测
    bt = Backtester(
        symbol="159928",
        start_date="2023-01-01",
        end_date="2025-12-31"
    )
    
    print("=== 均线交叉策略 ===")
    result = bt.run_ma_cross_strategy(5, 20)
    print(bt.generate_report())
