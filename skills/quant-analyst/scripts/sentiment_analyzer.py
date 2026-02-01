#!/usr/bin/env python3
"""
情绪分析模块 - sentiment_analyzer.py

用途：计算A股市场情绪温度，融合多维度情绪指标

情绪指标：
    - 融资余额变化
    - 换手率
    - 涨跌家数比
    - 成交额/历史均值
    - 北向资金流向
    
输出：
    情绪温度 0-100
    0-25: 恐惧区域（积极买入）
    25-40: 低估区域
    40-60: 中性区域
    60-75: 高估区域
    75-100: 贪婪区域（准备卖出）

使用示例：
    from sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze()
    print(f"情绪温度: {result['temperature']}")
    print(f"情绪状态: {result['status']}")

依赖：
    pip install akshare pandas numpy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False


class SentimentAnalyzer:
    """
    市场情绪分析器
    
    融合巴菲特"在别人恐惧时贪婪"的投资哲学
    """
    
    def __init__(self):
        self.indicators = {}
        self.weights = {
            "margin_change": 0.15,      # 融资余额变化
            "turnover_rate": 0.15,      # 换手率
            "advance_decline": 0.20,    # 涨跌家数比
            "volume_ratio": 0.20,       # 成交额比率
            "north_flow": 0.15,         # 北向资金
            "new_high_low": 0.15        # 新高新低比
        }
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """归一化到0-100"""
        if max_val == min_val:
            return 50
        normalized = (value - min_val) / (max_val - min_val) * 100
        return max(0, min(100, normalized))
    
    def _get_margin_sentiment(self) -> float:
        """融资余额变化情绪"""
        if not HAS_AKSHARE:
            return 50
        
        try:
            df = ak.stock_margin_sse()
            if len(df) < 5:
                return 50
            
            # 计算5日变化率
            recent = df.head(5)
            margin_values = recent['融资余额(元)'].astype(float)
            change_rate = (margin_values.iloc[0] - margin_values.iloc[-1]) / margin_values.iloc[-1] * 100
            
            # 变化率 -5% ~ +5% 映射到 0-100
            return self._normalize(change_rate, -5, 5)
        except:
            return 50
    
    def _get_turnover_sentiment(self) -> float:
        """换手率情绪"""
        if not HAS_AKSHARE:
            return 50
        
        try:
            df = ak.stock_zh_a_spot_em()
            avg_turnover = df['换手率'].astype(float).mean()
            
            # 换手率 1% ~ 5% 映射到 0-100
            return self._normalize(avg_turnover, 1, 5)
        except:
            return 50
    
    def _get_advance_decline_sentiment(self) -> float:
        """涨跌家数比情绪"""
        if not HAS_AKSHARE:
            return 50
        
        try:
            df = ak.stock_zh_a_spot_em()
            up_count = len(df[df['涨跌幅'].astype(float) > 0])
            down_count = len(df[df['涨跌幅'].astype(float) < 0])
            
            if down_count == 0:
                ratio = 10
            else:
                ratio = up_count / down_count
            
            # 比值 0.2 ~ 5 映射到 0-100
            return self._normalize(ratio, 0.2, 5)
        except:
            return 50
    
    def _get_volume_sentiment(self) -> float:
        """成交额相对历史的情绪"""
        if not HAS_AKSHARE:
            return 50
        
        try:
            # 获取上证指数成交额
            df = ak.stock_zh_index_daily(symbol="sh000001")
            if len(df) < 20:
                return 50
            
            recent = df.tail(20)
            today_vol = recent.iloc[-1]['volume']
            avg_vol = recent['volume'].mean()
            
            ratio = today_vol / avg_vol
            
            # 比值 0.5 ~ 2.0 映射到 0-100
            return self._normalize(ratio, 0.5, 2.0)
        except:
            return 50
    
    def _get_north_flow_sentiment(self) -> float:
        """北向资金情绪"""
        if not HAS_AKSHARE:
            return 50
        
        try:
            df = ak.stock_hsgt_north_net_flow_in_em()
            if len(df) < 5:
                return 50
            
            # 计算5日累计净流入
            recent = df.head(5)
            total_flow = recent['净流入'].astype(float).sum()
            
            # -500亿 ~ +500亿 映射到 0-100
            return self._normalize(total_flow, -500e8, 500e8)
        except:
            return 50
    
    def _get_new_high_low_sentiment(self) -> float:
        """新高新低比情绪"""
        if not HAS_AKSHARE:
            return 50
        
        try:
            df = ak.stock_zh_a_spot_em()
            
            # 简化：用涨幅>5%代替创新高
            new_high = len(df[df['涨跌幅'].astype(float) > 5])
            new_low = len(df[df['涨跌幅'].astype(float) < -5])
            
            total = new_high + new_low
            if total == 0:
                return 50
            
            ratio = new_high / total
            
            # 0 ~ 1 映射到 0-100
            return ratio * 100
        except:
            return 50
    
    def analyze(self) -> Dict[str, Any]:
        """
        执行情绪分析
        
        Returns:
            {
                "temperature": 0-100,
                "status": "恐惧"/"低估"/"中性"/"高估"/"贪婪",
                "signal": "积极买入"/"可以买入"/"持有观望"/"考虑减仓"/"准备卖出",
                "indicators": {...},
                "buffett_advice": "..."
            }
        """
        # 计算各项指标
        self.indicators = {
            "margin_change": self._get_margin_sentiment(),
            "turnover_rate": self._get_turnover_sentiment(),
            "advance_decline": self._get_advance_decline_sentiment(),
            "volume_ratio": self._get_volume_sentiment(),
            "north_flow": self._get_north_flow_sentiment(),
            "new_high_low": self._get_new_high_low_sentiment()
        }
        
        # 加权平均计算情绪温度
        temperature = sum(
            self.indicators[k] * self.weights[k] 
            for k in self.weights
        )
        
        # 状态判断
        if temperature < 25:
            status = "极度恐惧"
            signal = "积极买入"
            buffett = "现在正是'别人恐惧我贪婪'的时刻，这是最好的买入机会。"
        elif temperature < 40:
            status = "恐惧"
            signal = "可以买入"
            buffett = "市场情绪偏悲观，估值有吸引力，可以逐步建仓。"
        elif temperature < 60:
            status = "中性"
            signal = "持有观望"
            buffett = "市场情绪中性，保持现有仓位，等待更好的机会。"
        elif temperature < 75:
            status = "乐观"
            signal = "考虑减仓"
            buffett = "市场开始升温，需要保持警惕，可以考虑部分获利了结。"
        else:
            status = "极度贪婪"
            signal = "准备卖出"
            buffett = "现在是'别人贪婪我恐惧'的时刻，应该逐步减仓。"
        
        return {
            "temperature": round(temperature, 1),
            "status": status,
            "signal": signal,
            "indicators": self.indicators,
            "buffett_advice": buffett,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_temperature_bar(self, temperature: float) -> str:
        """生成情绪温度条可视化"""
        position = int(temperature / 100 * 50)
        bar = "─" * position + "●" + "─" * (50 - position)
        
        return f"""
情绪温度计:
  恐惧                     中性                     贪婪
  ├──────────────────────────────────────────────────┤
  [{bar}] {temperature:.1f}
  0         25         50         75        100
"""
    
    def generate_report(self) -> str:
        """生成情绪分析报告"""
        result = self.analyze()
        
        report = f"""
# A股市场情绪分析报告

**分析时间**: {result['timestamp']}

## 情绪温度

**当前温度**: {result['temperature']} / 100
**情绪状态**: {result['status']}
**操作信号**: {result['signal']}

{self.get_temperature_bar(result['temperature'])}

## 分项指标

| 指标 | 得分 | 权重 |
|------|------|------|
| 融资余额变化 | {result['indicators']['margin_change']:.1f} | {self.weights['margin_change']} |
| 换手率 | {result['indicators']['turnover_rate']:.1f} | {self.weights['turnover_rate']} |
| 涨跌家数比 | {result['indicators']['advance_decline']:.1f} | {self.weights['advance_decline']} |
| 成交量比率 | {result['indicators']['volume_ratio']:.1f} | {self.weights['volume_ratio']} |
| 北向资金 | {result['indicators']['north_flow']:.1f} | {self.weights['north_flow']} |
| 新高新低比 | {result['indicators']['new_high_low']:.1f} | {self.weights['new_high_low']} |

## 巴菲特视角

> {result['buffett_advice']}

---
*本报告仅供参考，不构成投资建议*
"""
        return report


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print(analyzer.generate_report())
