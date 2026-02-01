# 基础量化分析示例

> 使用quant-analyst技能进行ETF量化分析的入门示例

## 示例1：获取市场风向标

```python
from market_indicator import MarketIndicator

# 创建市场风向标实例
indicator = MarketIndicator()

# 获取完整市场概览
overview = indicator.get_market_overview()

# 打印主要指数估值
for idx in overview['indices']:
    print(f"{idx['index_name']}: PE={idx['pe']}, 百分位={idx['pe_percentile']}%")
```

**预期输出**：
```
沪深300: PE=14.31, 百分位=14.40%
上证指数: PE=16.90, 百分位=25.00%
创业板指: PE=52.87, 百分位=38.75%
```

---

## 示例2：情绪分析

```python
from sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze()

print(f"情绪温度: {result['temperature']}")
print(f"情绪状态: {result['status']}")
print(f"操作建议: {result['signal']}")
print(f"巴菲特视角: {result['buffett_advice']}")
```

---

## 示例3：单个指数估值查询

```python
from market_indicator import MarketIndicator

indicator = MarketIndicator()

# 查询沪深300估值
valuation = indicator.get_index_valuation("沪深300")
print(f"PE: {valuation['pe']}")
print(f"百分位: {valuation['pe_percentile']}%")
print(f"状态: {valuation['status']} {valuation['emoji']}")
print(f"信号: {valuation['signal']}")
```

---

## 数据来源说明

| 数据类型 | 来源 |
|----------|------|
| 指数PE/PB | 中证指数公司 (csindex.com.cn) |
| 融资融券 | 上交所官方披露 |
| 北向资金 | 港交所披露易 |

---

> [!CAUTION]
> 本示例仅供学习参考，不构成投资建议。
