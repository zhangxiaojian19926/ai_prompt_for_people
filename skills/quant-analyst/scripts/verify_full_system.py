#!/usr/bin/env python3
"""
全系统集成验证脚本 - verify_full_system.py
"""
import sys
import pandas as pd
from datetime import datetime
from data_fetcher import DataFetcher
from market_indicator import MarketIndicator
from backtest import Backtester

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def verify_macro():
    print_header("1. 宏观风向标 (ERP & Rf)")
    mi = MarketIndicator()
    overview = mi.get_market_overview()
    
    rf = overview.get('risk_free_rate', 0)
    erp = overview.get('erp', 0)
    
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"无风险利率 (Rf): {rf}%")
    print(f"股权风险溢价 (ERP): {erp}%")
    
    if erp > 4:
        print(">>> 评价: 极具投资价值 (ERP > 4%)")
    elif erp > 3:
        print(">>> 评价: 具备投资价值 (ERP > 3%)")
    elif erp < 0:
        print(">>> 评价: 市场显著高估 (ERP < 0%)")
    else:
        print(">>> 评价: 市场估值合理 (0% < ERP < 3%)")

def verify_fundamental(symbol="600519"):
    print_header(f"2. 个股基本面透视 ({symbol})")
    fetcher = DataFetcher()
    data = fetcher.get_stock_valuation(symbol)
    
    if data.get('error'):
        print(f"获取失败: {data['error']}")
        return

    print(f"股票名称: {data.get('name')} ({symbol})")
    print(f"总市值: {data.get('market_cap', 0):.2f} 亿")
    print("-" * 30)
    print(f"PE (TTM): {data.get('pe_ttm', 'N/A')}")
    print(f"PB:       {data.get('pb', 'N/A')}")
    print(f"ROE:      {data.get('roe', 'N/A')}%")
    print(f"PEG:      {data.get('peg', 'N/A')}")
    print(f"营收增长: {data.get('revenue_growth', 'N/A')}%")
    print(f"净利增长: {data.get('profit_growth', 'N/A')}%")

def verify_backtest(symbol="159928"):
    print_header(f"3. 策略回测与风控 ({symbol})")
    print("对比：[均线策略] vs [均线策略 + ATR止损]")
    
    bt = Backtester(symbol, "2024-01-01", "2024-12-31")
    
    # 1. 普通均线策略
    print("\n[A] 普通均线策略 (MA Cross)")
    res_a = bt.run_ma_cross_strategy()
    print(f"收益율: {res_a.total_return}%")
    print(f"最大回撤: {res_a.max_drawdown}%")
    print(f"夏普比率: {res_a.sharpe_ratio}")
    
    # 2. 带风控的回测
    # 需要手动调用带有stop_loss_atr参数的execute_backtest
    # 这里的run_ma_cross_strategy内部并没有暴露stop_loss_atr参数，
    # 为了验证，我们手动构造信号函数，调用_execute_backtest
    
    print("\n[B] 均线策略 + ATR动态风控 (2.0倍ATR)")
    
    # 重新初始化以清空状态
    bt = Backtester(symbol, "2024-01-01", "2024-12-31")
    
    # 定义均线信号函数 (与run_ma_cross_strategy一致)
    from backtest import Signal
    short_win, long_win = 5, 20
    def ma_signal(history, row):
        if len(history) < 2: return Signal.HOLD, ""
        prev = history.iloc[-2]
        curr_short = row.get(f'ma{short_win}')
        curr_long = row.get(f'ma{long_win}')
        prev_short = prev.get(f'ma{short_win}')
        prev_long = prev.get(f'ma{long_win}')
        
        if pd.isna(curr_short) or pd.isna(curr_long): return Signal.HOLD, ""
        
        if curr_short > curr_long and prev_short <= prev_long:
            return Signal.BUY, f"MA{short_win}上穿MA{long_win}"
        if curr_short < curr_long and prev_short >= prev_long:
            return Signal.SELL, f"MA{short_win}下穿MA{long_win}"
        return Signal.HOLD, ""

    # 执行带止损的回测
    res_b = bt._execute_backtest(ma_signal, stop_loss_atr=2.0)
    
    print(f"收益율: {res_b.total_return}%")
    print(f"最大回撤: {res_b.max_drawdown}%")
    print(f"夏普比率: {res_b.sharpe_ratio}")
    
    # 对比结果
    print("-" * 30)
    diff_ret = res_b.total_return - res_a.total_return
    diff_dd = res_a.max_drawdown - res_b.max_drawdown
    
    print(f"风控效果提升:")
    print(f"收益改善: {diff_ret:+.2f}%")
    print(f"回撤降低: {diff_dd:+.2f}%")
    
    # 检查是否有止损触发
    stops = [t for t in res_b.trades if "ATR" in t.reason]
    if stops:
        print(f"\n成功触发 {len(stops)} 次ATR止损:")
        for t in stops:
            print(f"  {t.date}: 价格{t.price:.3f} {t.reason}")

if __name__ == "__main__":
    try:
        verify_macro()
        verify_fundamental()
        verify_backtest()
        print("\n✅ 全系统验证通过")
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
