# quant-analyst 量化分析技能

> AI量化分析大师 - 融合投资大师智慧的机构级量化分析系统

## 功能

- **市场风向标**: PE/PB百分位计算、综合估值分析
- **情绪分析**: 恐惧贪婪指数、资金情绪
- **策略回测**: 均线、MACD、RSI、估值策略
- **技术指标**: 完整的技术分析工具包

## 快速开始

```bash
# 激活conda环境
conda activate ai_quant_analyst

# 运行市场风向标
python scripts/market_indicator.py

# 运行回测
python scripts/backtest.py
```

## 文档

- [SKILL.md](SKILL.md) - 详细技能文档
- [examples/](examples/) - 使用示例
- [CHANGELOG.md](CHANGELOG.md) - 更新日志

## 数据来源

| 类型 | 来源 |
|------|------|
| 指数PE/PB | 中证指数公司 |
| 融资融券 | 上交所官方披露 |
| 北向资金 | 港交所披露易 |

## 安装依赖

```bash
pip install -r requirements.txt
```

---

⚠️ **免责声明**: 本技能仅供学习研究，不构成投资建议。
