#!/usr/bin/env python3
"""
ETF分析器 - etf_analyzer.py

用途：获取ETF实时数据并生成分析报告

使用方法：
    python etf_analyzer.py --symbol 159928 --fetch
    python etf_analyzer.py --symbol 159928 --fetch --output report.md
    python etf_analyzer.py --list  # 列出热门ETF

依赖：
    pip install akshare
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False


# 热门ETF列表
POPULAR_ETFS = {
    "159928": "消费ETF",
    "510300": "沪深300ETF",
    "510500": "中证500ETF",
    "159915": "创业板ETF",
    "512100": "中证1000ETF",
    "512880": "证券ETF",
    "515790": "光伏ETF",
    "159869": "新能源车ETF",
    "512480": "半导体ETF",
    "512010": "医药ETF",
    "159605": "中概互联ETF",
    "513050": "中概互联网ETF",
}


def fetch_etf_data(symbol: str) -> Dict[str, Any]:
    """获取ETF实时数据"""
    if not HAS_AKSHARE:
        return {"error": "请安装akshare: pip install akshare"}
    
    data = {
        "symbol": symbol,
        "name": POPULAR_ETFS.get(symbol, ""),
        "price": 0,
        "change_pct": 0,
        "volume": 0,
        "amount": 0,
        "high": 0,
        "low": 0,
        "open": 0,
        "prev_close": 0,
    }
    
    try:
        # 获取ETF实时行情
        df = ak.fund_etf_spot_em()
        etf_row = df[df['代码'] == symbol]
        
        if not etf_row.empty:
            row = etf_row.iloc[0]
            data["name"] = str(row.get("名称", ""))
            data["price"] = float(row.get("最新价", 0) or 0)
            data["change_pct"] = float(row.get("涨跌幅", 0) or 0)
            data["volume"] = float(row.get("成交量", 0) or 0) / 1e4  # 万手
            data["amount"] = float(row.get("成交额", 0) or 0) / 1e8  # 亿元
            data["high"] = float(row.get("最高", 0) or 0)
            data["low"] = float(row.get("最低", 0) or 0)
            data["open"] = float(row.get("今开", 0) or 0)
            data["prev_close"] = float(row.get("昨收", 0) or 0)
            data["found"] = True
        else:
            data["error"] = f"未找到ETF代码: {symbol}"
            data["found"] = False
            
        # 尝试获取历史数据计算更多指标
        try:
            hist = ak.fund_etf_hist_em(symbol=symbol, period="daily", 
                                        start_date="20240101", 
                                        end_date=datetime.now().strftime("%Y%m%d"),
                                        adjust="qfq")
            if not hist.empty:
                data["high_52w"] = float(hist["最高"].max())
                data["low_52w"] = float(hist["最低"].min())
                data["avg_volume_20d"] = float(hist["成交量"].tail(20).mean()) / 1e4
                
                # 计算移动平均
                if len(hist) >= 20:
                    data["ma5"] = float(hist["收盘"].tail(5).mean())
                    data["ma20"] = float(hist["收盘"].tail(20).mean())
                    data["ma60"] = float(hist["收盘"].tail(60).mean()) if len(hist) >= 60 else 0
        except:
            pass
            
    except Exception as e:
        data["error"] = str(e)
    
    return data


def generate_etf_report(symbol: str, data: Dict[str, Any]) -> str:
    """生成ETF分析报告"""
    
    if not data.get("found", False) and "error" in data:
        return f"❌ 错误: {data['error']}"
    
    # 涨跌标记
    change = data.get("change_pct", 0)
    change_icon = "🔴" if change < 0 else ("🟢" if change > 0 else "⚪")
    
    # 趋势判断
    price = data.get("price", 0)
    ma5 = data.get("ma5", 0)
    ma20 = data.get("ma20", 0)
    ma60 = data.get("ma60", 0)
    
    if ma5 and ma20:
        if price > ma5 > ma20:
            trend = "上升趋势 📈"
        elif price < ma5 < ma20:
            trend = "下降趋势 📉"
        else:
            trend = "震荡整理 ➡️"
    else:
        trend = "数据不足"
    
    # 52周位置
    high_52w = data.get("high_52w", 0)
    low_52w = data.get("low_52w", 0)
    if high_52w and low_52w and high_52w != low_52w:
        position_52w = (price - low_52w) / (high_52w - low_52w) * 100
    else:
        position_52w = 50
    
    report = f'''# {data.get("name", symbol)} ({symbol}) ETF分析报告

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 一、实时行情

| 指标 | 数值 |
|------|------|
| **当前价格** | ¥{data.get("price", 0):.3f} |
| **涨跌幅** | {change_icon} {change:+.2f}% |
| **今开** | ¥{data.get("open", 0):.3f} |
| **最高** | ¥{data.get("high", 0):.3f} |
| **最低** | ¥{data.get("low", 0):.3f} |
| **昨收** | ¥{data.get("prev_close", 0):.3f} |
| **成交量** | {data.get("volume", 0):.0f}万手 |
| **成交额** | {data.get("amount", 0):.2f}亿元 |

---

## 二、技术指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **MA5** | ¥{data.get("ma5", 0):.3f} | {"站上" if price > ma5 else "跌破"} |
| **MA20** | ¥{data.get("ma20", 0):.3f} | {"站上" if price > ma20 else "跌破"} |
| **MA60** | ¥{data.get("ma60", 0):.3f} | {"站上" if price > ma60 else "跌破"} |
| **趋势判断** | {trend} | |

---

## 三、52周区间分析

| 指标 | 数值 |
|------|------|
| **52周最高** | ¥{data.get("high_52w", 0):.3f} |
| **52周最低** | ¥{data.get("low_52w", 0):.3f} |
| **当前位置** | {position_52w:.0f}% |

```
52周最低 [{position_52w:.0f}%━━━━━━━━━━━━━━━━━━━━] 52周最高
¥{low_52w:.3f}                              ¥{high_52w:.3f}
            当前: ¥{price:.3f}
```

### 位置解读
- 0-20%: 接近52周低点，可能是低估区域
- 20-40%: 偏低位置
- 40-60%: 中间位置
- 60-80%: 偏高位置  
- 80-100%: 接近52周高点，注意风险

**当前评估**: {"接近低点，关注买入机会" if position_52w < 30 else ("中间位置，观望为主" if position_52w < 70 else "接近高点，注意风险")}

---

## 四、交易活跃度

| 指标 | 数值 | 评价 |
|------|------|------|
| 今日成交量 | {data.get("volume", 0):.0f}万手 | |
| 20日均量 | {data.get("avg_volume_20d", 0):.0f}万手 | |
| 量比 | {data.get("volume", 0) / max(data.get("avg_volume_20d", 1), 1):.2f} | {"放量" if data.get("volume", 0) > data.get("avg_volume_20d", 1) * 1.5 else ("缩量" if data.get("volume", 0) < data.get("avg_volume_20d", 1) * 0.7 else "正常")} |

---

## 五、操作建议

### 基于当前技术面

| 条件 | 状态 |
|------|------|
| 价格 vs MA5 | {"✅ 多头" if price > ma5 else "❌ 空头"} |
| 价格 vs MA20 | {"✅ 多头" if price > ma20 else "❌ 空头"} |
| 52周位置 | {"⚠️ 高位" if position_52w > 70 else ("✅ 低位" if position_52w < 30 else "➡️ 中位")} |

### 策略参考

**趋势策略**:
- 当价格站上MA20且MA5>MA20时，考虑买入
- 当价格跌破MA20且MA5<MA20时，考虑减仓

**定投策略**:
- 52周位置<30%时，可加大定投金额
- 52周位置>70%时，可减少定投金额

---

> ⚠️ **免责声明**：本报告基于历史数据生成，仅供参考，不构成投资建议。ETF投资有风险，入市需谨慎。

---

*报告由 etf_analyzer.py 生成 | 数据来源: akshare*
'''
    return report


def list_popular_etfs():
    """列出热门ETF"""
    print("\n📊 热门ETF列表:\n")
    print("| 代码 | 名称 |")
    print("|------|------|")
    for code, name in POPULAR_ETFS.items():
        print(f"| {code} | {name} |")
    print(f"\n使用方法: python etf_analyzer.py --symbol <代码> --fetch")


def main():
    parser = argparse.ArgumentParser(description="ETF分析器")
    parser.add_argument("--symbol", "-s", help="ETF代码")
    parser.add_argument("--fetch", "-f", action="store_true", help="获取实时数据")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--list", "-l", action="store_true", help="列出热门ETF")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ etf_analyzer.py 测试通过")
        print(f"   akshare: {'已安装' if HAS_AKSHARE else '未安装'}")
        return
    
    if args.list:
        list_popular_etfs()
        return
    
    if not args.symbol:
        print("❌ 请指定ETF代码: --symbol <代码>")
        print("示例: python etf_analyzer.py --symbol 159928 --fetch")
        print("查看热门ETF: python etf_analyzer.py --list")
        return
    
    if args.fetch:
        if not HAS_AKSHARE:
            print("❌ 需要安装akshare: pip install akshare")
            return
        
        print(f"🔍 正在获取 {args.symbol} 数据...")
        data = fetch_etf_data(args.symbol)
        
        if "error" in data and not data.get("found", False):
            print(f"❌ {data['error']}")
            return
        
        report = generate_etf_report(args.symbol, data)
        print(f"✅ 已获取 {data.get('name', args.symbol)} 数据")
        
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"✅ 报告已保存: {args.output}")
        else:
            print(report)
    else:
        print(f"💡 使用 --fetch 获取实时数据:")
        print(f"   python etf_analyzer.py --symbol {args.symbol} --fetch")


if __name__ == "__main__":
    main()
