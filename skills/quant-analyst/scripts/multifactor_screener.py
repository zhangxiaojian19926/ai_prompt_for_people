#!/usr/bin/env python3
"""
多因子选股策略 - multifactor_screener.py

基于 质量(Quality) + 价值(Value) + 成长(Growth) + 动量(Momentum) 四大维度
筛选"好行业、好公司、好价格"的投资标的。
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from data_fetcher import DataFetcher
from indicators import TechnicalIndicators

class MultiFactorScreener:
    def __init__(self):
        self.fetcher = DataFetcher()
        self.default_pool = [
            # 消费
            "600519", # 贵州茅台
            "000858", # 五粮液
            "600887", # 伊利股份
            "000568", # 泸州老窖
            # 科技/新能源
            "300750", # 宁德时代
            "002594", # 比亚迪
            "601012", # 隆基绿能
            "600438", # 通威股份
            # 金融
            "600036", # 招商银行
            "601318", # 中国平安
            "600030", # 中信证券
            # 医疗
            "600276", # 恒瑞医药
            "300015", # 爱尔眼科
            "300760", # 迈瑞医疗
            # 制造
            "600031", # 三一重工
            "000333", # 美的集团
            "000651", # 格力电器
        ]
        
    def get_stock_factors(self, symbol: str) -> Dict[str, Any]:
        """获取单只股票的所有因子数据"""
        # 1. 获取基本面估值 & 财务数据
        valuation = self.fetcher.get_stock_valuation(symbol)
        if valuation.get("error"):
            return None
            
        # 2. 获取技术面数据 (用于动量)
        # 获取最近3个月数据计算趋势
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - pd.Timedelta(days=100)).strftime("%Y-%m-%d")
        kline = self.fetcher.get_history_kline(symbol, start_date, end_date)
        
        rsi = ma60 = price = 0
        if not kline.empty and len(kline) > 60:
            ti = TechnicalIndicators(kline)
            df_ti = ti.add_all_indicators() # 假设indicators.py里有add_all_indicators
            # 如果indicators里没有add_all_indicators，我们需要手动计算
            # 这里简单计算
            latest = df_ti.iloc[-1]
            price = latest['close']
            # 计算RSI/MA如果indicators已计算则直接用，否则需计算
            # 为稳健起见，我们在screener里简单计算动量
            closes = kline['close']
            ma60 = closes.rolling(60).mean().iloc[-1]
            
            # RSI简易计算
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        return {
            "symbol": symbol,
            "name": valuation.get("name"),
            # 质量因子
            "roe": valuation.get("roe"), # 净资产收益率
            "npm": valuation.get("net_profit_margin"), # 净利率
            # 价值因子
            "pe": valuation.get("pe_ttm"),
            "peg": valuation.get("peg"),
            # 成长因子
            "rev_growth": valuation.get("revenue_growth"), # 营收增长
            "profit_growth": valuation.get("profit_growth"), # 净利增长
            # 动量因子
            "price": price,
            "ma60": ma60,
            "rsi": rsi,
            "trend": "bull" if price > ma60 else "bear"
        }

    def screen(self, symbols: List[str] = None, limit: int = None) -> pd.DataFrame:
        """
        执行选股筛选
        
        Args:
            symbols: 股票代码列表，默认使用 default_pool
            limit: 限制扫描数量，用于快速测试
        """
        if symbols is None:
            symbols = self.default_pool
            
        if limit:
            symbols = symbols[:limit]
            
        print(f"正在扫描 {len(symbols)} 只股票...")
        results = []
        
        for i, code in enumerate(symbols):
            try:
                print(f"[{i+1}/{len(symbols)}] 分析 {code} ...")
                factors = self.get_stock_factors(code)
                if factors:
                    results.append(factors)
            except Exception as e:
                print(f"处理 {code} 失败: {e}")
                
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results)
        
        # 计算综合得分 (0-100)
        # 简单评分逻辑: 
        # ROE > 15 (+20分)
        # PE < 35 (+20分)
        # 增长 > 10% (+20分)
        # 趋势向上 (+20分)
        # RSI适中 (+20分)
        
        scores = []
        for _, row in df.iterrows():
            score = 0
            # 质量
            if row['roe'] and row['roe'] > 15: score += 20
            elif row['roe'] and row['roe'] > 10: score += 10
            
            # 价值
            if row['pe'] and 0 < row['pe'] < 30: score += 20
            elif row['pe'] and row['pe'] < 45: score += 10
            
            # 成长
            if row['rev_growth'] and row['rev_growth'] > 15: score += 20
            elif row['rev_growth'] and row['rev_growth'] > 5: score += 10
            
            # 趋势
            if row['price'] > row['ma60']: score += 20
            
            # 动量 (RSI不做极端)
            if row['rsi'] and 40 < row['rsi'] < 70: score += 20
            elif row['rsi'] and 30 < row['rsi'] < 80: score += 10
            
            scores.append(score)
            
        df['score'] = scores
        return df.sort_values('score', ascending=False)

if __name__ == "__main__":
    screener = MultiFactorScreener()
    # 演示仅扫描前3只，避免超时
    df = screener.screen(limit=3)
    
    print("\n====== 多因子选股结果演示 ======")
    cols = ['name', 'symbol', 'score', 'pe', 'roe', 'rev_growth', 'trend']
    if not df.empty:
        print(df[cols].head(10).to_string(index=False))
        
        print("\n[选股逻辑]")
        print("1. 质量: ROE > 15%")
        print("2. 价值: PE < 30")
        print("3. 成长: 营收增长 > 15%")
        print("4. 趋势: 站上60日均线")
        print("5. 动量: RSI在40-70之间")
    else:
        print("未获取到有效数据")
