# 情绪分析示例

> 使用quant-analyst情绪分析系统判断市场恐惧贪婪程度

## 情绪温度计

### 获取当前情绪温度

```python
from sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze()

print(f"情绪温度: {result['temperature']} / 100")
print(f"情绪状态: {result['status']}")
print(f"操作建议: {result['signal']}")
```

### 情绪温度解读

| 温度区间 | 状态 | 操作建议 |
|----------|------|----------|
| 0-25 | 极度恐惧 | 🟢 积极买入 |
| 25-40 | 恐惧 | 🟡 可以买入 |
| 40-60 | 中性 | ⚪ 持有观望 |
| 60-75 | 乐观 | 🟠 考虑减仓 |
| 75-100 | 极度贪婪 | 🔴 准备卖出 |

---

## 分项情绪指标

```python
result = analyzer.analyze()

for indicator, score in result['indicators'].items():
    print(f"{indicator}: {score:.1f}")
```

**主要指标**：
- `margin_change`: 融资余额变化（来源: 上交所）
- `turnover_rate`: 平均换手率
- `advance_decline`: 涨跌家数比
- `volume_ratio`: 成交额/20日均值
- `north_flow`: 北向资金5日净流入
- `new_high_low`: 新高新低比

---

## 情绪逆向策略

> "别人恐惧我贪婪，别人贪婪我恐惧" —— 巴菲特

```python
def sentiment_contrarian(temperature):
    if temperature < 25:
        return "极度恐惧 → 重仓买入(80%)"
    elif temperature < 40:
        return "恐惧 → 逐步买入(60%)"
    elif temperature < 60:
        return "中性 → 持有观望(50%)"
    elif temperature < 75:
        return "乐观 → 逐步卖出(30%)"
    else:
        return "极度贪婪 → 清仓离场(10%)"

result = analyzer.analyze()
action = sentiment_contrarian(result['temperature'])
print(f"当前温度: {result['temperature']} → {action}")
```

---

## 生成情绪报告

```python
analyzer = SentimentAnalyzer()
report = analyzer.generate_report()
print(report)
```

---

## 数据来源

| 指标 | 数据来源 |
|------|----------|
| 融资余额 | 上交所官方披露 (sse.com.cn) |
| 北向资金 | 港交所披露易 (hkex.com.hk) |
| 涨跌家数 | 上交所/深交所实时行情 |
| 成交额 | 交易所实时数据 |

---

> [!NOTE]
> 情绪指标是辅助工具，需结合估值、基本面综合判断。
