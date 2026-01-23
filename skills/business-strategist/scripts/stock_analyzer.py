#!/usr/bin/env python3
"""
股票分析器 v2.0 - stock_analyzer.py

用途：获取股票实时数据并生成投资分析报告

使用方法：
    # 获取A股实时数据
    python stock_analyzer.py --symbol 600519 --fetch
    
    # 仅生成框架（无需网络）
    python stock_analyzer.py --symbol 600519
    
    # 保存报告
    python stock_analyzer.py --symbol 600519 --fetch --output report.md

依赖：
    pip install akshare  # A股数据源（免费）

参数：
    --symbol, -s    股票代码
    --market, -m    市场: A(A股), US(美股), HK(港股)
    --fetch, -f     获取实时数据
    --output, -o    输出文件
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 尝试导入akshare
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

# 市场信息
MARKETS = {
    "A": {"name": "A股", "currency": "CNY"},
    "US": {"name": "美股", "currency": "USD"},
    "HK": {"name": "港股", "currency": "HKD"}
}

def detect_market(symbol: str) -> str:
    """自动检测市场"""
    if symbol.isdigit():
        if len(symbol) == 6:
            return "A"
        elif len(symbol) == 5:
            return "HK"
    return "US"


def fetch_a_stock_data(symbol: str) -> Dict[str, Any]:
    """获取A股实时数据"""
    if not HAS_AKSHARE:
        return {"error": "请安装akshare: pip install akshare"}
    
    data = {
        "symbol": symbol,
        "name": "",
        "price": 0,
        "change_pct": 0,
        "pe": 0,
        "pb": 0,
        "market_cap": 0,
        "volume": 0,
        "turnover": 0,
        "high_52w": 0,
        "low_52w": 0,
        "industry": "",
        "roa": 0,
        "roe": 0,
        "gross_margin": 0,
        "net_margin": 0,
        "debt_ratio": 0,
    }
    
    try:
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        stock_row = df[df['代码'] == symbol]
        
        if not stock_row.empty:
            row = stock_row.iloc[0]
            data["name"] = row.get("名称", "")
            data["price"] = float(row.get("最新价", 0) or 0)
            data["change_pct"] = float(row.get("涨跌幅", 0) or 0)
            data["pe"] = float(row.get("市盈率-动态", 0) or 0)
            data["pb"] = float(row.get("市净率", 0) or 0)
            data["market_cap"] = float(row.get("总市值", 0) or 0) / 1e8  # 转为亿
            data["volume"] = float(row.get("成交量", 0) or 0) / 1e4  # 转为万手
            data["turnover"] = float(row.get("换手率", 0) or 0)
        
        # 获取财务指标
        try:
            fin_df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
            if not fin_df.empty:
                latest = fin_df.iloc[0]
                data["roe"] = float(latest.get("净资产收益率", 0) or 0)
                data["gross_margin"] = float(latest.get("销售毛利率", 0) or 0)
                data["net_margin"] = float(latest.get("销售净利率", 0) or 0)
                data["debt_ratio"] = float(latest.get("资产负债率", 0) or 0)
        except:
            pass
        
        # 获取行业信息
        try:
            info_df = ak.stock_individual_info_em(symbol=symbol)
            if not info_df.empty:
                for _, row in info_df.iterrows():
                    if row['item'] == '行业':
                        data["industry"] = row['value']
                        break
        except:
            pass
            
    except Exception as e:
        data["error"] = str(e)
    
    return data


def generate_report_with_data(symbol: str, market: str, data: Dict[str, Any]) -> str:
    """生成包含实时数据的分析报告"""
    market_info = MARKETS.get(market.upper(), MARKETS["A"])
    
    # 估值状态判断
    pe = data.get("pe", 0)
    if pe > 0:
        if pe < 15:
            pe_status = "低估"
        elif pe < 25:
            pe_status = "合理"
        elif pe < 40:
            pe_status = "偏高"
        else:
            pe_status = "高估"
    else:
        pe_status = "N/A"
    
    # 涨跌标记
    change = data.get("change_pct", 0)
    change_icon = "🔴" if change < 0 else ("🟢" if change > 0 else "⚪")
    
    report = f'''# {data.get("name", symbol)} ({symbol}) 投资分析报告

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**市场**: {market_info["name"]}
**行业**: {data.get("industry", "待补充")}

---

## 一、实时行情

| 指标 | 数值 | 说明 |
|------|------|------|
| **当前价格** | ¥{data.get("price", 0):.2f} | {change_icon} {change:+.2f}% |
| **总市值** | {data.get("market_cap", 0):.0f}亿 | |
| **成交量** | {data.get("volume", 0):.0f}万手 | 换手率 {data.get("turnover", 0):.2f}% |

---

## 二、估值分析

| 指标 | 当前值 | 状态 |
|------|--------|------|
| **市盈率(PE)** | {data.get("pe", 0):.1f} | {pe_status} |
| **市净率(PB)** | {data.get("pb", 0):.2f} | |

### 估值计算
```
当前PE: {data.get("pe", 0):.1f}
如果PE回归到15倍，目标价约: ¥{data.get("price", 0) * 15 / max(data.get("pe", 1), 1):.2f}
如果PE回归到25倍，目标价约: ¥{data.get("price", 0) * 25 / max(data.get("pe", 1), 1):.2f}
```

---

## 三、财务健康度

| 指标 | 数值 | 评价 |
|------|------|------|
| **净资产收益率(ROE)** | {data.get("roe", 0):.1f}% | {"优秀" if data.get("roe", 0) > 15 else ("良好" if data.get("roe", 0) > 10 else "一般")} |
| **销售毛利率** | {data.get("gross_margin", 0):.1f}% | {"高利润" if data.get("gross_margin", 0) > 30 else "一般"} |
| **销售净利率** | {data.get("net_margin", 0):.1f}% | |
| **资产负债率** | {data.get("debt_ratio", 0):.1f}% | {"低杠杆" if data.get("debt_ratio", 0) < 40 else ("适中" if data.get("debt_ratio", 0) < 60 else "高杠杆")} |

---

## 四、投资哲学检验

### 巴菲特检验
| 检查项 | 状态 | 说明 |
|--------|------|------|
| 业务是否能理解？ | ⬜ | [待评估] |
| 是否有持续竞争优势？ | {"✅" if data.get("roe", 0) > 15 else "⬜"} | ROE {data.get("roe", 0):.1f}% |
| 管理层是否诚信能干？ | ⬜ | [待评估] |
| 价格是否有安全边际？ | {"✅" if pe_status in ["低估", "合理"] else "⬜"} | PE {pe_status} |

### 段永平检验
- **Right Business**: {data.get("industry", "")}行业，毛利率{data.get("gross_margin", 0):.1f}%
- **Right People**: [待评估管理层]
- **Right Price**: 当前PE {data.get("pe", 0):.1f}

---

## 五、风险提示

| 风险类型 | 描述 | 等级 |
|---------|------|------|
| 估值风险 | PE {data.get("pe", 0):.1f}，{pe_status} | {"🔴高" if pe_status == "高估" else ("🟡中" if pe_status == "偏高" else "🟢低")} |
| 财务风险 | 负债率 {data.get("debt_ratio", 0):.1f}% | {"🔴高" if data.get("debt_ratio", 0) > 60 else "🟢低"} |
| 流动性风险 | 换手率 {data.get("turnover", 0):.2f}% | {"🟢低" if data.get("turnover", 0) > 1 else "🟡中"} |

---

## 六、投资结论

### 快速评分
| 维度 | 评分 |
|------|------|
| 盈利能力 | {"⭐⭐⭐⭐⭐" if data.get("roe", 0) > 20 else ("⭐⭐⭐⭐" if data.get("roe", 0) > 15 else ("⭐⭐⭐" if data.get("roe", 0) > 10 else "⭐⭐"))} |
| 估值水平 | {"⭐⭐⭐⭐⭐" if pe_status == "低估" else ("⭐⭐⭐⭐" if pe_status == "合理" else ("⭐⭐⭐" if pe_status == "偏高" else "⭐⭐"))} |
| 财务健康 | {"⭐⭐⭐⭐⭐" if data.get("debt_ratio", 0) < 30 else ("⭐⭐⭐⭐" if data.get("debt_ratio", 0) < 50 else "⭐⭐⭐")} |

### 建议操作
基于当前数据的初步判断：
- PE {data.get("pe", 0):.1f} ({pe_status})
- ROE {data.get("roe", 0):.1f}%
- 负债率 {data.get("debt_ratio", 0):.1f}%

> ⚠️ **免责声明**：本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。

---

*报告由 stock_analyzer.py v2.0 生成 | 数据来源: akshare*
'''
    return report


def generate_template(symbol: str, market: str) -> str:
    """生成空白报告框架（无需网络）"""
    market_info = MARKETS.get(market.upper(), MARKETS["A"])
    
    return f'''# {symbol} 投资分析报告

**生成日期**: {datetime.now().strftime("%Y-%m-%d")}
**市场**: {market_info["name"]}

> 💡 使用 `--fetch` 参数获取实时数据：
> `python stock_analyzer.py --symbol {symbol} --fetch`

---

## 一、基本信息

| 项目 | 内容 |
|------|------|
| 股票代码 | {symbol} |
| 公司名称 | [待获取] |
| 行业 | [待获取] |
| 市值 | [待获取] |

---

## 二、估值数据

| 指标 | 数值 |
|------|------|
| 当前价格 | [待获取] |
| PE | [待获取] |
| PB | [待获取] |

---

## 使用说明

1. 安装依赖: `pip install akshare`
2. 获取数据: `python stock_analyzer.py --symbol {symbol} --fetch`
3. 保存报告: `python stock_analyzer.py --symbol {symbol} --fetch --output report.md`

*框架由 stock_analyzer.py 生成*
'''


def main():
    parser = argparse.ArgumentParser(description="股票分析器 v2.0")
    parser.add_argument("--symbol", "-s", help="股票代码")
    parser.add_argument("--market", "-m", choices=["A", "US", "HK"], help="市场")
    parser.add_argument("--fetch", "-f", action="store_true", help="获取实时数据")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ stock_analyzer.py v2.0 测试通过")
        print(f"   akshare: {'已安装' if HAS_AKSHARE else '未安装'}")
        return
    
    if not args.symbol:
        print("❌ 请指定股票代码: --symbol <代码>")
        print("示例: python stock_analyzer.py --symbol 600519 --fetch")
        return
    
    market = args.market or detect_market(args.symbol)
    
    if args.fetch:
        if market == "A":
            if not HAS_AKSHARE:
                print("❌ 需要安装akshare: pip install akshare")
                return
            
            print(f"🔍 正在获取 {args.symbol} 数据...")
            data = fetch_a_stock_data(args.symbol)
            
            if "error" in data:
                print(f"⚠️ 获取数据时出现问题: {data['error']}")
            
            report = generate_report_with_data(args.symbol, market, data)
            print(f"✅ 已获取 {data.get('name', args.symbol)} 数据")
        else:
            print(f"⚠️ 暂不支持{MARKETS[market]['name']}实时数据，生成框架...")
            report = generate_template(args.symbol, market)
    else:
        report = generate_template(args.symbol, market)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ 报告已保存: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
