# 策略回测示例

> 使用quant-analyst回测系统验证交易策略的历史表现

## 回测5种策略

### 1. 均线交叉策略

```python
from backtest import Backtester

bt = Backtester(
    symbol="159928",          # 消费ETF
    start_date="2023-01-01",
    end_date="2025-12-31",
    initial_capital=100000    # 10万初始资金
)

# 运行5日/20日均线交叉策略
result = bt.run_ma_cross_strategy(short=5, long=20)

# 输出回测报告
print(bt.generate_report())
```

**策略逻辑**：
- 买入：5日均线上穿20日均线
- 卖出：5日均线下穿20日均线

---

### 2. MACD策略

```python
bt = Backtester("159928", "2023-01-01", "2025-12-31")
result = bt.run_macd_strategy()
print(bt.generate_report())
```

**策略逻辑**：
- 买入：DIF上穿DEA（金叉）
- 卖出：DIF下穿DEA（死叉）

---

### 3. RSI策略

```python
bt = Backtester("159928", "2023-01-01", "2025-12-31")
result = bt.run_rsi_strategy(oversold=30, overbought=70)
print(bt.generate_report())
```

**策略逻辑**：
- 买入：RSI < 30（超卖）
- 卖出：RSI > 70（超买）

---

### 4. 布林带策略

```python
bt = Backtester("159928", "2023-01-01", "2025-12-31")
result = bt.run_bollinger_strategy()
print(bt.generate_report())
```

**策略逻辑**：
- 买入：价格跌破下轨
- 卖出：价格突破上轨

---

### 5. 估值策略

```python
bt = Backtester("159928", "2023-01-01", "2025-12-31")
result = bt.run_value_invest_strategy(pe_buy=20, pe_sell=70)
print(bt.generate_report())
```

**策略逻辑**：
- 买入：PE百分位 < 20%
- 卖出：PE百分位 > 70%

---

## 回测指标解读

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| 总收益率 | 策略总回报 | > 基准 |
| 年化收益 | 年均复合增长 | > 15% |
| 夏普比率 | 风险调整收益 | > 1.0 |
| 最大回撤 | 最大亏损幅度 | < 30% |
| 胜率 | 盈利交易占比 | > 50% |
| 盈亏比 | 平均盈利/亏损 | > 1.5 |

---

> [!CAUTION]
> 回测结果不代表真实收益，历史表现不能预测未来。
