#!/usr/bin/env python3
"""
情绪分析模块 - sentiment_analyzer.py (v2)

使用动态历史百分位代替固定范围归一化，使情绪指标更具自适应性。
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any

# scipy是可选依赖
try:
    from scipy.stats import percentileofscore
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    # 自定义percentileofscore实现
    def percentileofscore(a, score, kind='rank'):
        a = np.array(a)
        n = len(a)
        if n == 0:
            return 50.0
        left = np.sum(a < score)
        right = np.sum(a <= score)
        return 100 * (left + right) / (2 * n)

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

class SentimentAnalyzer:
    """
    市场情绪分析器 (v2 - 动态百分位)
    """
    def __init__(self, history_days: int = 250):
        self.history_days = history_days
        self.indicators = {}
        self.weights = {
            "margin_change": 0.20,      # 融资余额变化
            "advance_decline": 0.20,    # 涨跌家数比
            "volume_ratio": 0.15,       # 成交额比率
            "north_flow": 0.15,         # 北向资金
            "new_high_low": 0.15,       # 新高新低比
            "turnover_rate": 0.15,      # 换手率
        }

    def _get_percentile_score(self, series: pd.Series) -> float:
        """计算序列中最后一个值的历史百分位 (0-100)"""
        if series.empty or len(series) < 20:
            return 50.0  # 数据不足时返回中性值
        
        series = series.dropna()
        if series.empty:
            return 50.0

        latest_value = series.iloc[-1]
        score = percentileofscore(series, latest_value, kind='rank')
        return float(score)

    def _get_margin_sentiment(self) -> float:
        """融资余额5日变化率的历史百分位"""
        if not HAS_AKSHARE: return 50.0
        try:
            df = ak.stock_margin_sse(start_date="20200101", end_date="20990101")
            df = df.iloc[::-1].reset_index(drop=True) # Reverse to chronological order
            df['融资余额(元)'] = pd.to_numeric(df['融资余额(元)'])
            # 计算5日变化率
            margin_change_rate = df['融资余额(元)'].pct_change(periods=5) * 100
            return self._get_percentile_score(margin_change_rate)
        except:
            return 50.0

    def _get_advance_decline_sentiment(self) -> float:
        """涨跌比的历史百分位"""
        if not HAS_AKSHARE: return 50.0
        try:
            # 获取A股市场两市(沪深)每日的涨跌数
            df = ak.stock_zbgc_em()
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').tail(self.history_days)
            # 计算涨跌比
            df['ratio'] = df['上涨家数'] / (df['下跌家数'] + 1)
            return self._get_percentile_score(df['ratio'])
        except:
            return 50.0
            
    def _get_volume_sentiment(self) -> float:
        """上证指数成交额的历史百分位"""
        if not HAS_AKSHARE: return 50.0
        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            df = df.tail(self.history_days)
            return self._get_percentile_score(df['volume'])
        except:
            return 50.0

    def _get_north_flow_sentiment(self) -> float:
        """北向资金5日净流入的历史百分位"""
        if not HAS_AKSHARE: return 50.0
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向资金")
            df = df.iloc[::-1].reset_index(drop=True)
            df['净流入'] = pd.to_numeric(df['净流入'])
            # 计算5日滚动净流入
            net_flow_5d = df['净流入'].rolling(5).sum()
            return self._get_percentile_score(net_flow_5d)
        except:
            return 50.0

    def _get_new_high_low_sentiment(self) -> float:
        """创历史新高/新低股票数量比值的历史百分位"""
        if not HAS_AKSHARE: return 50.0
        try:
            high_df = ak.stock_lx_stock_tj_em(symbol="创历史新高")
            low_df = ak.stock_lx_stock_tj_em(symbol="创历史新低")
            merged = pd.merge(high_df[['日期', '数量']], low_df[['日期', '数量']], on="日期", suffixes=('_high', '_low'))
            merged['日期'] = pd.to_datetime(merged['日期'])
            merged = merged.sort_values('日期').tail(self.history_days)
            # 计算 high / (high+low)
            merged['ratio'] = merged['数量_high'] / (merged['数量_high'] + merged['数量_low'] + 1)
            return self._get_percentile_score(merged['ratio'])
        except:
            return 50.0

    def _get_turnover_sentiment(self) -> float:
        """上证指数换手率的历史百分位"""
        if not HAS_AKSHARE: return 50.0
        try:
            # akshare没有直接提供指数换手率历史，此处用成交额代替作为近似
            df = ak.stock_zh_index_daily(symbol="sh000001")
            df = df.tail(self.history_days)
            return self._get_percentile_score(df['amount'])
        except:
            return 50.0

    def analyze(self) -> Dict[str, Any]:
        print("正在执行情绪分析(动态百分位模型)...")
        self.indicators = {
            "margin_change": self._get_margin_sentiment(),
            "advance_decline": self._get_advance_decline_sentiment(),
            "volume_ratio": self._get_volume_sentiment(),
            "north_flow": self._get_north_flow_sentiment(),
            "new_high_low": self._get_new_high_low_sentiment(),
            "turnover_rate": self._get_turnover_sentiment(),
        }
        
        temperature = sum(self.indicators[k] * self.weights[k] for k in self.weights if self.indicators.get(k) is not None)
        
        if temperature < 25: status, signal, buffett = "极度恐惧", "积极买入", "市场极度悲观，是逆向投资的良机。"
        elif temperature < 40: status, signal, buffett = "恐惧", "可以买入", "市场情绪偏悲观，估值有吸引力，可逐步建仓。"
        elif temperature < 60: status, signal, buffett = "中性", "持有观望", "市场情绪中性，保持现有仓位，等待更好机会。"
        elif temperature < 75: status, signal, buffett = "乐观", "考虑减仓", "市场开始升温，需保持警惕，可部分获利了结。"
        else: status, signal, buffett = "极度贪婪", "准备卖出", "市场情绪狂热，应逐步减仓，落袋为安。"
        
        return {"temperature": round(temperature, 1), "status": status, "signal": signal, "indicators": self.indicators, "buffett_advice": buffett, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    def generate_report(self) -> str:
        result = self.analyze()
        bar_pos = int(result['temperature'] / 100 * 50); bar = "─" * bar_pos + "●" + "─" * (50 - bar_pos)
        indicator_rows = "\n".join([f"| {k:<12} | {v:6.1f} | {self.weights[k]:<4} |" for k, v in result['indicators'].items()])
        
        return f"""
# A股市场情绪分析报告 (v2)
**分析时间**: {result['timestamp']}
## 情绪温度: {result['temperature']} / 100
**情绪状态**: {result['status']}
**操作信号**: {result['signal']}
### 情绪温度计
恐惧{' '*20}中性{' '*20}贪婪
├──────────────────────────────────────────────────┤
[{bar}]
0{' '*10}25{' '*10}50{' '*10}75{' '*10}100
## 分项指标 (历史百分位)
| 指标 | 得分 | 权重 |
|:---|:---|:---|
{indicator_rows}
## 巴菲特视角
> {result['buffett_advice']}
---
*本报告基于各指标在过去约一年内的历史位置计算，仅供参考，不构成投资建议*
"""

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print(analyzer.generate_report())
