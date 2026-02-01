#!/usr/bin/env python3
"""
数据获取模块 - data_fetcher.py

用途：获取A股/ETF的实时行情、历史K线、估值数据、资金流向等

使用示例：
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    
    # 获取实时行情
    realtime = fetcher.get_realtime_quote("159928")
    
    # 获取历史K线
    history = fetcher.get_history_kline("159928", "2023-01-01", "2025-12-31")
    
    # 获取估值数据
    valuation = fetcher.get_valuation("000932")  # 中证主要消费指数

依赖：
    pip install akshare pandas numpy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告: 请安装akshare: pip install akshare")


class DataFetcher:
    """数据获取器 - 统一接口获取各类金融数据"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 缓存5分钟
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache_time:
            return False
        return (datetime.now() - self.cache_time[key]).seconds < self.cache_duration
    
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            symbol: 股票/ETF代码，如 "159928", "600519"
            
        Returns:
            包含价格、成交量、涨跌幅等的字典
        """
        if not HAS_AKSHARE:
            return {"error": "请安装akshare"}
        
        cache_key = f"realtime_{symbol}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        data = {
            "symbol": symbol,
            "name": "",
            "price": 0,
            "change_pct": 0,
            "volume": 0,
            "amount": 0,
            "high": 0,
            "low": 0,
            "open": 0,
            "prev_close": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # 判断是ETF还是股票
            if symbol.startswith(("51", "56", "58", "15", "16")):
                # ETF
                df = ak.fund_etf_spot_em()
                row = df[df['代码'] == symbol]
                if not row.empty:
                    row = row.iloc[0]
                    data["name"] = str(row.get("名称", ""))
                    data["price"] = float(row.get("最新价", 0) or 0)
                    data["change_pct"] = float(row.get("涨跌幅", 0) or 0)
                    data["volume"] = float(row.get("成交量", 0) or 0)
                    data["amount"] = float(row.get("成交额", 0) or 0)
                    data["high"] = float(row.get("最高", 0) or 0)
                    data["low"] = float(row.get("最低", 0) or 0)
                    data["open"] = float(row.get("今开", 0) or 0)
                    data["prev_close"] = float(row.get("昨收", 0) or 0)
            else:
                # 股票
                df = ak.stock_zh_a_spot_em()
                row = df[df['代码'] == symbol]
                if not row.empty:
                    row = row.iloc[0]
                    data["name"] = str(row.get("名称", ""))
                    data["price"] = float(row.get("最新价", 0) or 0)
                    data["change_pct"] = float(row.get("涨跌幅", 0) or 0)
                    data["volume"] = float(row.get("成交量", 0) or 0)
                    data["amount"] = float(row.get("成交额", 0) or 0)
                    data["high"] = float(row.get("最高", 0) or 0)
                    data["low"] = float(row.get("最低", 0) or 0)
                    data["open"] = float(row.get("今开", 0) or 0)
                    data["prev_close"] = float(row.get("昨收", 0) or 0)
            
            self.cache[cache_key] = data
            self.cache_time[cache_key] = datetime.now()
            
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def get_history_kline(self, symbol: str, start_date: str, end_date: str, 
                          period: str = "daily", adjust: str = "qfq") -> pd.DataFrame:
        """
        获取历史K线数据
        
        Args:
            symbol: 股票/ETF代码
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
            period: 周期 "daily"/"weekly"/"monthly"
            adjust: 复权类型 "qfq"前复权/"hfq"后复权/""不复权
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume, amount
        """
        if not HAS_AKSHARE:
            return pd.DataFrame()
        
        try:
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")
            
            if symbol.startswith(("51", "56", "58", "15", "16")):
                # ETF
                df = ak.fund_etf_hist_em(
                    symbol=symbol,
                    period=period,
                    start_date=start,
                    end_date=end,
                    adjust=adjust
                )
            else:
                # 股票
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period=period,
                    start_date=start,
                    end_date=end,
                    adjust=adjust
                )
            
            # 标准化列名
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "change_pct"
            })
            
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_valuation(self, index_code: str) -> Dict[str, Any]:
        """
        获取指数估值数据
        
        Args:
            index_code: 指数代码，如 "000932"(中证主要消费)
            
        Returns:
            包含PE、PB及其历史分位的字典
        """
        # 此功能需要通过网络搜索获取，返回模板数据
        return {
            "index_code": index_code,
            "pe": 0,
            "pe_percentile": 0,
            "pb": 0,
            "pb_percentile": 0,
            "note": "请使用search_web获取最新估值数据"
        }
    
    def get_north_flow(self, days: int = 5) -> pd.DataFrame:
        """
        获取北向资金流向
        
        Args:
            days: 获取最近N天数据
            
        Returns:
            DataFrame with north bound fund flow
        """
        if not HAS_AKSHARE:
            return pd.DataFrame()
        
        try:
            df = ak.stock_hsgt_north_net_flow_in_em()
            df = df.head(days)
            return df
        except Exception as e:
            print(f"获取北向资金失败: {e}")
            return pd.DataFrame()
    
    def get_margin_balance(self) -> Dict[str, Any]:
        """获取融资融券余额"""
        if not HAS_AKSHARE:
            return {"error": "请安装akshare"}
        
        try:
            df = ak.stock_margin_sse()
            if not df.empty:
                latest = df.iloc[0]
                return {
                    "date": str(latest.get("信用交易日期", "")),
                    "margin_balance": float(latest.get("融资余额(元)", 0)),
                    "short_balance": float(latest.get("融券余量金额(元)", 0))
                }
        except Exception as e:
            return {"error": str(e)}
        
        return {}
    
    def get_market_breadth(self) -> Dict[str, Any]:
        """
        获取市场广度（涨跌家数）
        
        Returns:
            up_count: 上涨家数
            down_count: 下跌家数
            ratio: 涨跌比
        """
        if not HAS_AKSHARE:
            return {"error": "请安装akshare"}
        
        try:
            df = ak.stock_zh_a_spot_em()
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            flat_count = len(df[df['涨跌幅'] == 0])
            
            ratio = up_count / down_count if down_count > 0 else float('inf')
            
            return {
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "ratio": round(ratio, 2),
                "total": len(df)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_turnover_rate(self, symbol: str) -> float:
        """获取换手率"""
        if not HAS_AKSHARE:
            return 0
        
        try:
            if symbol.startswith(("51", "56", "58", "15", "16")):
                df = ak.fund_etf_spot_em()
                row = df[df['代码'] == symbol]
            else:
                df = ak.stock_zh_a_spot_em()
                row = df[df['代码'] == symbol]
            
            if not row.empty:
                return float(row.iloc[0].get('换手率', 0) or 0)
        except:
            pass
        return 0


# 便捷函数
def fetch_realtime(symbol: str) -> Dict[str, Any]:
    """快捷获取实时行情"""
    return DataFetcher().get_realtime_quote(symbol)


def fetch_history(symbol: str, days: int = 365) -> pd.DataFrame:
    """快捷获取历史数据"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return DataFetcher().get_history_kline(symbol, start_date, end_date)


if __name__ == "__main__":
    # 测试代码
    fetcher = DataFetcher()
    
    print("=== 测试实时行情 ===")
    quote = fetcher.get_realtime_quote("159928")
    print(f"消费ETF: {quote}")
    
    print("\n=== 测试市场广度 ===")
    breadth = fetcher.get_market_breadth()
    print(f"涨跌家数: {breadth}")
    
    print("\n=== 测试北向资金 ===")
    north = fetcher.get_north_flow(5)
    print(north.head())
