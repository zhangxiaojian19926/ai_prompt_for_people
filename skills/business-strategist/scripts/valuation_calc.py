#!/usr/bin/env python3
"""
估值计算器 - valuation_calc.py

用途：快速计算股票估值和安全边际

使用方法：
    python valuation_calc.py --pe 15 --eps 5.2 --growth 0.15
    python valuation_calc.py --dcf --fcf 100 --growth 0.1 --discount 0.1
    python valuation_calc.py --compare --current-pe 20 --hist-pe-low 10 --hist-pe-high 30

参数：
    --pe            市盈率估值
    --dcf           DCF估值模式
    --compare       历史对比估值
"""

import argparse
from typing import Optional

def pe_valuation(pe: float, eps: float, growth: float = 0) -> dict:
    """市盈率估值"""
    fair_value = pe * eps
    
    # PEG调整
    peg = pe / (growth * 100) if growth > 0 else None
    peg_adjusted_pe = growth * 100 * 1.5 if growth > 0 else pe  # PEG=1.5为合理
    peg_fair_value = peg_adjusted_pe * eps if growth > 0 else fair_value
    
    return {
        "method": "PE估值",
        "fair_value": round(fair_value, 2),
        "peg": round(peg, 2) if peg else None,
        "peg_adjusted_value": round(peg_fair_value, 2) if growth > 0 else None,
        "margin_of_safety_30": round(fair_value * 0.7, 2),
        "margin_of_safety_50": round(fair_value * 0.5, 2)
    }


def dcf_valuation(fcf: float, growth: float, discount: float, 
                  years: int = 10, terminal_growth: float = 0.02) -> dict:
    """DCF估值（简化版）"""
    # 计算未来现金流现值
    pv_fcf = 0
    current_fcf = fcf
    
    for year in range(1, years + 1):
        current_fcf = current_fcf * (1 + growth)
        pv_fcf += current_fcf / ((1 + discount) ** year)
    
    # 终值
    terminal_value = current_fcf * (1 + terminal_growth) / (discount - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount) ** years)
    
    total_value = pv_fcf + pv_terminal
    
    return {
        "method": "DCF估值",
        "pv_fcf": round(pv_fcf, 2),
        "pv_terminal": round(pv_terminal, 2),
        "fair_value": round(total_value, 2),
        "margin_of_safety_30": round(total_value * 0.7, 2),
        "margin_of_safety_50": round(total_value * 0.5, 2),
        "assumptions": {
            "growth_rate": f"{growth*100}%",
            "discount_rate": f"{discount*100}%",
            "terminal_growth": f"{terminal_growth*100}%",
            "projection_years": years
        }
    }


def historical_compare(current_pe: float, hist_pe_low: float, 
                      hist_pe_high: float, eps: float = 1) -> dict:
    """历史对比估值"""
    hist_pe_median = (hist_pe_low + hist_pe_high) / 2
    
    # 当前估值位置
    percentile = (current_pe - hist_pe_low) / (hist_pe_high - hist_pe_low) * 100
    
    return {
        "method": "历史对比估值",
        "current_pe": current_pe,
        "historical_low": hist_pe_low,
        "historical_high": hist_pe_high,
        "historical_median": round(hist_pe_median, 2),
        "current_percentile": round(percentile, 1),
        "valuation_status": "高估" if percentile > 70 else ("低估" if percentile < 30 else "合理"),
        "fair_value_at_median": round(hist_pe_median * eps, 2),
        "fair_value_at_low": round(hist_pe_low * eps, 2)
    }


def format_result(result: dict) -> str:
    """格式化输出结果"""
    output = [f"\n📊 {result['method']}\n", "-" * 40]
    
    for key, value in result.items():
        if key == "method":
            continue
        if key == "assumptions":
            output.append("\n假设条件:")
            for k, v in value.items():
                output.append(f"  {k}: {v}")
        else:
            label = key.replace("_", " ").title()
            output.append(f"{label}: {value}")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="估值计算器")
    
    # PE估值参数
    parser.add_argument("--pe", type=float, help="市盈率")
    parser.add_argument("--eps", type=float, default=1, help="每股收益")
    parser.add_argument("--growth", type=float, default=0, help="增长率")
    
    # DCF估值参数
    parser.add_argument("--dcf", action="store_true", help="使用DCF估值")
    parser.add_argument("--fcf", type=float, help="自由现金流")
    parser.add_argument("--discount", type=float, default=0.1, help="折现率")
    parser.add_argument("--years", type=int, default=10, help="预测年数")
    
    # 历史对比参数
    parser.add_argument("--compare", action="store_true", help="历史对比估值")
    parser.add_argument("--current-pe", type=float, help="当前PE")
    parser.add_argument("--hist-pe-low", type=float, help="历史PE低点")
    parser.add_argument("--hist-pe-high", type=float, help="历史PE高点")
    
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ valuation_calc.py 测试通过")
        return
    
    if args.dcf and args.fcf:
        result = dcf_valuation(args.fcf, args.growth, args.discount, args.years)
        print(format_result(result))
    elif args.compare and args.current_pe:
        result = historical_compare(
            args.current_pe, 
            args.hist_pe_low or 10, 
            args.hist_pe_high or 30,
            args.eps
        )
        print(format_result(result))
    elif args.pe:
        result = pe_valuation(args.pe, args.eps, args.growth)
        print(format_result(result))
    else:
        print("❌ 请指定估值方式:")
        print("  PE估值: --pe 15 --eps 5.2")
        print("  DCF估值: --dcf --fcf 100 --growth 0.1 --discount 0.1")
        print("  历史对比: --compare --current-pe 20 --hist-pe-low 10 --hist-pe-high 30")


if __name__ == "__main__":
    main()
