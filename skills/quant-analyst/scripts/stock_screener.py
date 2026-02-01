#!/usr/bin/env python3
"""
A股股票筛选器 - stock_screener.py

根据SKILL.md中定义的A股策略，实现多种选股功能。
"""

import pandas as pd
import akshare as ak
from typing import List, Dict, Any
from tqdm import tqdm

class StockScreener:
    """
    A股股票筛选器
    """
    def __init__(self):
        """
        初始化时获取全市场股票的实时数据
        """
        try:
            print("正在获取全市场A股实时数据，请稍候...")
            # 获取所有A股的实时行情数据，包括PE、PB、市值、换手率等
            self.market_data = ak.stock_zh_a_spot_em()
            print(f"成功获取 {len(self.market_data)} 只A股的数据。")
        except Exception as e:
            print(f"错误：获取A股列表失败: {e}")
            self.market_data = pd.DataFrame()

    def _get_financial_indicators(self, stocks: List[str]) -> pd.DataFrame:
        """
        获取指定股票列表的主要财务指标
        """
        if not stocks:
            return pd.DataFrame()
        
        print(f"正在为 {len(stocks)} 只股票获取财务指标...")
        all_indicators = []
        for symbol in tqdm(stocks, desc="获取财务数据"):
            try:
                # 获取指定股票的财务分析主要指标
                df = ak.stock_financial_analysis_indicator(stock=symbol)
                # 选择最新的财报 (通常是第一行)
                latest_indicators = df.iloc[0:1].copy()
                latest_indicators['代码'] = symbol
                all_indicators.append(latest_indicators)
            except Exception as e:
                # print(f"警告：获取 {symbol} 的财务数据失败: {e}")
                pass
        
        if not all_indicators:
            return pd.DataFrame()
            
        return pd.concat(all_indicators, ignore_index=True)

    def screen_value_growth(self, pe_max: float = 30, roe_min: float = 15, growth_min: float = 20) -> pd.DataFrame:
        """
        价值成长策略筛选
        
        筛选条件:
        - PE < pe_max
        - ROE > roe_min (%)
        - 营收增速 > growth_min (%)
        """
        if self.market_data.empty:
            return pd.DataFrame()

        # 1. 初步筛选 (基于市盈率和非科创板/北交所)
        print(f"1. 初步筛选: PE < {pe_max} ...")
        pre_filtered = self.market_data[
            (self.market_data['市盈率(动态)'] > 0) &
            (self.market_data['市盈率(动态)'] < pe_max) &
            (~self.market_data['代码'].str.startswith(('68', '8', '4'))) # 排除科创板/北交所
        ]
        
        stocks_to_check = pre_filtered['代码'].tolist()
        
        # 2. 获取财务指标
        financials = self._get_financial_indicators(stocks_to_check)
        if financials.empty:
            print("警告: 未能获取任何股票的财务数据。")
            return pd.DataFrame()

        # 3. 合并数据
        merged_df = pd.merge(pre_filtered, financials, on='代码')

        # 4. 二次筛选 (基于ROE和营收增速)
        print(f"2. 详细筛选: ROE > {roe_min}%, 营收增速 > {growth_min}% ...")
        
        # akshare返回的字段名可能包含"净资产收益率(%)"或"净资产收益率-ROE(%)"
        roe_col = next((col for col in financials.columns if '净资产收益率' in col), None)
        gpr_col = next((col for col in financials.columns if '营业收入增长率' in col), None)

        if not roe_col or not gpr_col:
            print(f"错误: 无法在财务数据中找到 '净资产收益率' 或 '营业收入增长率' 字段。")
            return pd.DataFrame()

        final_selection = merged_df[
            (merged_df[roe_col] > roe_min) &
            (merged_df[gpr_col] > growth_min)
        ]

        # 5. 整理输出
        output_cols = ['代码', '名称', '最新价', '市盈率(动态)', roe_col, gpr_col, '总市值', '行业']
        return final_selection[output_cols].rename(columns={
            '市盈率(动态)': 'PE',
            roe_col: 'ROE(%)',
            gpr_col: '营收增速(%)'
        }).sort_values(by='ROE(%)', ascending=False)

    def screen_high_dividend(self, dividend_yield_min: float = 4, pe_max: float = 20, market_cap_min: float = 200e8) -> pd.DataFrame:
        """
        高股息策略筛选
        
        筛选条件:
        - 股息率 > dividend_yield_min (%)
        - PE < pe_max
        - 市值 > market_cap_min
        """
        if self.market_data.empty:
            return pd.DataFrame()
            
        print(f"筛选条件: 股息率 > {dividend_yield_min}%, PE < {pe_max}, 市值 > {market_cap_min/1e8:.0f}亿")
        
        selection = self.market_data[
            (self.market_data['股息率(%)'] > dividend_yield_min) &
            (self.market_data['市盈率(动态)'] > 0) &
            (self.market_data['市盈率(动态)'] < pe_max) &
            (self.market_data['总市值'] > market_cap_min) &
            (~self.market_data['名称'].str.contains('ST'))
        ]
        
        output_cols = ['代码', '名称', '最新价', '股息率(%)', '市盈率(动态)', '总市值', '行业']
        return selection[output_cols].rename(columns={
            '市盈率(动态)': 'PE'
        }).sort_values(by='股息率(%)', ascending=False)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="A股股票筛选器.")
    parser.add_argument(
        "strategy", 
        type=str, 
        choices=['value_growth', 'high_dividend'], 
        help="要执行的筛选策略: 'value_growth' 或 'high_dividend'"
    )
    # 价值成长策略参数
    parser.add_argument("--pe_max", type=float, default=30, help="[价值成长] 最大市盈率")
    parser.add_argument("--roe_min", type=float, default=15, help="[价值成长] 最小净资产收益率(%)")
    parser.add_argument("--growth_min", type=float, default=20, help="[价值成长] 最小营收增速(%)")
    
    # 高股息策略参数
    parser.add_argument("--dividend_yield_min", type=float, default=4, help="[高股息] 最小股息率(%)")
    parser.add_argument("--market_cap_min", type=float, default=200, help="[高股息] 最小市值（亿）")

    args = parser.parse_args()

    screener = StockScreener()

    if not screener.market_data.empty:
        if args.strategy == 'value_growth':
            print("\n" + "="*50)
            print("执行价值成长策略筛选...")
            print("="*50)
            results = screener.screen_value_growth(
                pe_max=args.pe_max, 
                roe_min=args.roe_min, 
                growth_min=args.growth_min
            )
            if not results.empty:
                print("\n✅ 价值成长股筛选结果:")
                print(results.to_markdown(index=False))
            else:
                print("\n❌ 未找到符合条件的价值成长股。")

        elif args.strategy == 'high_dividend':
            print("\n" + "="*50)
            print("执行高股息策略筛选...")
            print("="*50)
            results = screener.screen_high_dividend(
                dividend_yield_min=args.dividend_yield_min, 
                pe_max=args.pe_max, 
                market_cap_min=args.market_cap_min * 1e8
            )
            if not results.empty:
                print("\n✅ 高股息股筛选结果:")
                print(results.to_markdown(index=False))
            else:
                print("\n❌ 未找到符合条件的高股息股。")
    else:
        print("无法执行筛选，因为市场数据加载失败。")
