#!/usr/bin/env python3
"""
技术指标计算模块 - indicators.py

用途：计算各类技术分析指标

指标列表：
    - 移动平均线 (MA, EMA)
    - MACD
    - RSI
    - KDJ
    - 布林带 (BOLL)
    - ATR
    - OBV

使用示例：
    from indicators import TechnicalIndicators
    
    ti = TechnicalIndicators(df)
    df = ti.add_all_indicators()

依赖：
    pip install pandas numpy
"""

import pandas as pd
import numpy as np
from typing import Optional, List

try:
    from config import get_config
except ImportError:
    # Fallback for running script standalone
    def get_config(section=None):
        configs = {
            "ma": {"short": 5, "medium": 10, "long": 20, "trend": 60, "super_long": 120},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "rsi": {"period": 14, "oversold": 30, "overbought": 70},
            "bollinger": {"period": 20, "std_dev": 2},
        }
        if section:
            return configs.get(section, {})
        return configs


class TechnicalIndicators:
    """技术指标计算器"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化
        
        Args:
            df: 包含OHLCV数据的DataFrame
                必须包含: open, high, low, close, volume
        """
        self.df = df.copy()
        # 加载配置
        self.ma_config = get_config("ma")
        self.macd_config = get_config("macd")
        self.rsi_config = get_config("rsi")
        self.bollinger_config = get_config("bollinger")
    
    def add_ma(self, periods: list = None) -> pd.DataFrame:
        """添加简单移动平均线"""
        if periods is None:
            periods = list(self.ma_config.values())
        
        for period in periods:
            self.df[f'ma{period}'] = self.df['close'].rolling(period).mean()
        return self.df
    
    def add_ema(self, periods: list = None) -> pd.DataFrame:
        """添加指数移动平均线"""
        if periods is None:
            periods = [self.macd_config.get("fast", 12), self.macd_config.get("slow", 26)]
            
        for period in periods:
            self.df[f'ema{period}'] = self.df['close'].ewm(span=period, adjust=False).mean()
        return self.df
    
    def add_macd(self, fast: int = None, slow: int = None, signal: int = None) -> pd.DataFrame:
        """
        添加MACD指标
        """
        fast = fast or self.macd_config.get("fast", 12)
        slow = slow or self.macd_config.get("slow", 26)
        signal = signal or self.macd_config.get("signal", 9)

        # 确保EMA已计算
        if f'ema{fast}' not in self.df.columns or f'ema{slow}' not in self.df.columns:
            self.add_ema(periods=[fast, slow])
        
        self.df['dif'] = self.df[f'ema{fast}'] - self.df[f'ema{slow}']
        self.df['dea'] = self.df['dif'].ewm(span=signal, adjust=False).mean()
        self.df['macd'] = 2 * (self.df['dif'] - self.df['dea'])
        
        return self.df
    
    def add_rsi(self, period: int = None) -> pd.DataFrame:
        """
        添加RSI指标
        """
        period = period or self.rsi_config.get("period", 14)
        
        delta = self.df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / (loss + 1e-10)
        self.df[f'rsi{period}'] = 100 - (100 / (1 + rs))
        
        return self.df
    
    def add_kdj(self, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        添加KDJ指标 (参数暂不从配置读取)
        """
        low_n = self.df['low'].rolling(n).min()
        high_n = self.df['high'].rolling(n).max()
        
        rsv = (self.df['close'] - low_n) / (high_n - low_n + 1e-10) * 100
        
        self.df['k'] = rsv.ewm(span=m1, adjust=False).mean()
        self.df['d'] = self.df['k'].ewm(span=m2, adjust=False).mean()
        self.df['j'] = 3 * self.df['k'] - 2 * self.df['d']
        
        return self.df
    
    def add_bollinger(self, period: int = None, std_dev: float = None) -> pd.DataFrame:
        """
        添加布林带
        """
        period = period or self.bollinger_config.get("period", 20)
        std_dev = std_dev or self.bollinger_config.get("std_dev", 2.0)
        
        self.df['boll_mid'] = self.df['close'].rolling(period).mean()
        self.df['boll_std'] = self.df['close'].rolling(period).std()
        self.df['boll_upper'] = self.df['boll_mid'] + std_dev * self.df['boll_std']
        self.df['boll_lower'] = self.df['boll_mid'] - std_dev * self.df['boll_std']
        
        return self.df
    
    def add_atr(self, period: int = 14) -> pd.DataFrame:
        """
        添加ATR (参数暂不从配置读取)
        """
        high_low = self.df['high'] - self.df['low']
        high_close = abs(self.df['high'] - self.df['close'].shift())
        low_close = abs(self.df['low'] - self.df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['atr'] = tr.rolling(period).mean()
        
        return self.df
    
    def add_obv(self) -> pd.DataFrame:
        """添加OBV (On Balance Volume)"""
        obv = [0]
        for i in range(1, len(self.df)):
            if self.df['close'].iloc[i] > self.df['close'].iloc[i-1]:
                obv.append(obv[-1] + self.df['volume'].iloc[i])
            elif self.df['close'].iloc[i] < self.df['close'].iloc[i-1]:
                obv.append(obv[-1] - self.df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        self.df['obv'] = obv
        return self.df
    
    def add_volume_ma(self, periods: list = None) -> pd.DataFrame:
        """添加成交量均线"""
        if periods is None:
            # 使用MA配置中的短期和中期均线周期
            periods = [self.ma_config.get("short", 5), self.ma_config.get("medium", 10), self.ma_config.get("long", 20)]
            
        for period in periods:
            self.df[f'vol_ma{period}'] = self.df['volume'].rolling(period).mean()
        return self.df
    
    def add_price_change(self) -> pd.DataFrame:
        """添加价格变化指标"""
        self.df['change'] = self.df['close'].diff()
        self.df['change_pct'] = self.df['close'].pct_change() * 100
        self.df['amplitude'] = (self.df['high'] - self.df['low']) / self.df['close'].shift() * 100
        return self.df
    
    def add_all_indicators(self) -> pd.DataFrame:
        """添加所有指标"""
        self.add_ma()
        self.add_ema() # 在add_macd中被调用
        self.add_macd()
        self.add_rsi()
        self.add_kdj()
        self.add_bollinger()
        self.add_atr()
        self.add_obv()
        self.add_volume_ma()
        self.add_price_change()
        return self.df
    
    def get_signal_summary(self) -> dict:
        """获取技术信号汇总"""
        if self.df.empty or len(self.df) < 2:
            return {}
        
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        signals = {
            'ma_signal': self._get_ma_signal(latest),
            'macd_signal': self._get_macd_signal(latest, prev),
            'rsi_signal': self._get_rsi_signal(latest),
            'kdj_signal': self._get_kdj_signal(latest),
            'boll_signal': self._get_boll_signal(latest)
        }
        
        buy_count = sum(1 for s in signals.values() if s == '买入')
        sell_count = sum(1 for s in signals.values() if s == '卖出')
        
        if buy_count >= 3:
            signals['overall'] = '强烈买入'
        elif buy_count >= 2:
            signals['overall'] = '买入'
        elif sell_count >= 3:
            signals['overall'] = '强烈卖出'
        elif sell_count >= 2:
            signals['overall'] = '卖出'
        else:
            signals['overall'] = '中性'
        
        return signals
    
    def _get_ma_signal(self, row) -> str:
        """均线信号"""
        short = self.ma_config.get("short", 5)
        long = self.ma_config.get("long", 20)
        if f'ma{short}' in row and f'ma{long}' in row:
            if row[f'ma{short}'] > row[f'ma{long}']:
                return '买入'
            elif row[f'ma{short}'] < row[f'ma{long}']:
                return '卖出'
        return '中性'
    
    def _get_macd_signal(self, row, prev) -> str:
        """MACD信号"""
        if 'dif' in row and 'dea' in row and 'dif' in prev and 'dea' in prev:
            if prev['dif'] <= prev['dea'] and row['dif'] > row['dea']:
                return '买入'
            elif prev['dif'] >= prev['dea'] and row['dif'] < row['dea']:
                return '卖出'
        return '中性'
    
    def _get_rsi_signal(self, row) -> str:
        """RSI信号"""
        period = self.rsi_config.get("period", 14)
        oversold = self.rsi_config.get("oversold", 30)
        overbought = self.rsi_config.get("overbought", 70)
        
        if f'rsi{period}' in row:
            if row[f'rsi{period}'] < oversold:
                return '买入'
            elif row[f'rsi{period}'] > overbought:
                return '卖出'
        return '中性'
    
    def _get_kdj_signal(self, row) -> str:
        """KDJ信号"""
        if 'j' in row:
            if row['j'] < 0:
                return '买入'
            elif row['j'] > 100:
                return '卖出'
        return '中性'
    
    def _get_boll_signal(self, row) -> str:
        """布林带信号"""
        if 'boll_lower' in row and 'boll_upper' in row:
            if row['close'] < row['boll_lower']:
                return '买入'
            elif row['close'] > row['boll_upper']:
                return '卖出'
        return '中性'


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """便捷函数：计算所有指标"""
    return TechnicalIndicators(df).add_all_indicators()


if __name__ == "__main__":
    import numpy as np
    
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100)
    close = 100 * np.cumprod(1 + np.random.randn(100) * 0.02)
    
    df = pd.DataFrame({
        'date': dates,
        'open': close * 0.99,
        'high': close * 1.02,
        'low': close * 0.98,
        'close': close,
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    ti = TechnicalIndicators(df)
    result = ti.add_all_indicators()
    
    print("指标计算完成，共", len(result.columns), "列")
    print(result.tail())
    print("\n最新技术信号:")
    signals = ti.get_signal_summary()
    for k, v in signals.items():
        print(f"  {k}: {v}")
