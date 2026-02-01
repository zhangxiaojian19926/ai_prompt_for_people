# ETF估值分析示例

> 使用quant-analyst对ETF进行估值分析和投资决策

## 消费ETF分析案例 (159928)

### 步骤1：获取实时行情

```python
from data_fetcher import DataFetcher

fetcher = DataFetcher()
quote = fetcher.get_realtime_quote("159928")

print(f"名称: {quote['name']}")
print(f"当前价: {quote['price']}")
print(f"涨跌幅: {quote['change_pct']}%")
print(f"成交额: {quote['amount']/1e8:.2f}亿")
```

### 步骤2：计算技术指标

```python
from data_fetcher import DataFetcher
from indicators import TechnicalIndicators

fetcher = DataFetcher()
df = fetcher.get_history_kline("159928", "2024-01-01", "2026-01-31")

# 计算所有技术指标
ti = TechnicalIndicators(df)
df = ti.add_all_indicators()

# 获取技术信号汇总
signals = ti.get_signal_summary()
print(f"均线信号: {signals['ma_signal']}")
print(f"MACD信号: {signals['macd_signal']}")
print(f"综合信号: {signals['overall']}")
```

### 步骤3：估值定位

```python
from market_indicator import MarketIndicator

indicator = MarketIndicator()

# 获取消费行业相关指数估值
valuation = indicator.get_index_valuation("沪深300")

print(f"参考指数PE: {valuation['pe']}")
print(f"历史百分位: {valuation['pe_percentile']}%")
print(f"估值状态: {valuation['status']}")

# 根据估值判断仓位
if valuation['pe_percentile'] < 30:
    print("建议: 处于低估区域，可以考虑买入")
elif valuation['pe_percentile'] > 70:
    print("建议: 处于高估区域，考虑减仓")
else:
    print("建议: 估值合理，持有观望")
```

---

## 估值定投策略

根据PE百分位动态调整定投金额：

| PE百分位 | 定投系数 | 说明 |
|----------|----------|------|
| < 20% | 2.0x | 极度低估，加倍定投 |
| 20-40% | 1.5x | 低估，增加定投 |
| 40-60% | 1.0x | 合理，正常定投 |
| 60-80% | 0.5x | 高估，减少定投 |
| > 80% | 0x | 极度高估，暂停定投 |

---

> [!NOTE]
> 数据来源: 中证指数公司、上交所、深交所
