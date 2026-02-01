#!/usr/bin/env python3
"""
估值数据管理模块 - valuation_data.py

用途：管理指数历史估值数据，支持多数据源获取和本地缓存

功能：
    - 从AKShare获取历史PE/PB数据
    - 本地CSV缓存管理
    - 自动更新过期数据
    - 多数据源容错

数据来源：
    1. AKShare (index_value_hist_funddb)
    2. 本地CSV缓存
    
作者：AI量化分析大师
版本：1.0.0
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

try:
    import akshare as ak
except ImportError:
    ak = None

# 数据缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "valuation_cache")


class ValuationDataManager:
    """
    估值数据管理器
    
    负责获取、缓存和管理指数历史估值数据
    """
    
    # 支持的指数列表
    SUPPORTED_INDICES = {
        "沪深300": {"code": "000300", "funddb_name": "沪深300"},
        "上证指数": {"code": "000001", "funddb_name": "上证指数"},
        "创业板指": {"code": "399006", "funddb_name": "创业板指"},
        "中证500": {"code": "000905", "funddb_name": "中证500"},
        "上证50": {"code": "000016", "funddb_name": "上证50"},
        "中证1000": {"code": "000852", "funddb_name": "中证1000"},
    }
    
    # 缓存有效期（天）
    CACHE_EXPIRY_DAYS = 1
    
    def __init__(self, cache_dir: str = None):
        """
        初始化数据管理器
        
        Args:
            cache_dir: 缓存目录路径，默认为 data/valuation_cache
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self._ensure_cache_dir()
        self.data_source = "unknown"
        self.last_update = None
        self.is_realtime = False
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, index_name: str) -> str:
        """获取指数缓存文件路径"""
        safe_name = index_name.replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_name}_valuation.csv")
    
    def _get_meta_path(self, index_name: str) -> str:
        """获取元数据文件路径"""
        safe_name = index_name.replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_name}_meta.json")
    
    def _is_cache_valid(self, index_name: str) -> bool:
        """检查缓存是否有效"""
        meta_path = self._get_meta_path(index_name)
        cache_path = self._get_cache_path(index_name)
        
        if not os.path.exists(cache_path) or not os.path.exists(meta_path):
            return False
        
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            last_update = datetime.fromisoformat(meta.get("last_update", "2000-01-01"))
            expiry = datetime.now() - timedelta(days=self.CACHE_EXPIRY_DAYS)
            
            return last_update > expiry
        except Exception:
            return False
    
    def _save_cache(self, index_name: str, df: pd.DataFrame, source: str):
        """保存数据到缓存"""
        cache_path = self._get_cache_path(index_name)
        meta_path = self._get_meta_path(index_name)
        
        # 保存数据
        df.to_csv(cache_path, index=False, encoding='utf-8')
        
        # 保存元数据
        meta = {
            "index_name": index_name,
            "last_update": datetime.now().isoformat(),
            "source": source,
            "rows": len(df),
            "date_range": {
                "start": str(df.iloc[0].get('date', df.index[0]) if len(df) > 0 else None),
                "end": str(df.iloc[-1].get('date', df.index[-1]) if len(df) > 0 else None)
            }
        }
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    def _load_cache(self, index_name: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        cache_path = self._get_cache_path(index_name)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            df = pd.read_csv(cache_path, encoding='utf-8')
            self.data_source = "local_cache"
            return df
        except Exception:
            return None
    
    def fetch_from_akshare(self, index_name: str) -> Optional[pd.DataFrame]:
        """
        从AKShare获取历史估值数据
        
        Args:
            index_name: 指数名称
            
        Returns:
            包含PE历史数据的DataFrame，失败返回None
        """
        if ak is None:
            return None
        
        funddb_name = self.SUPPORTED_INDICES.get(index_name, {}).get("funddb_name", index_name)
        
        try:
            # 尝试 index_value_hist_funddb 接口
            df = ak.index_value_hist_funddb(symbol=funddb_name, indicator="市盈率")
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    "日期": "date",
                    "市盈率": "pe",
                    "市净率": "pb"
                })
                
                # 确保有必要的列
                if "pe" in df.columns:
                    self.data_source = "akshare_funddb"
                    self.is_realtime = True
                    self.last_update = datetime.now()
                    return df
        except Exception as e:
            pass
        
        try:
            # 备用：尝试其他AKShare接口
            # index_zh_a_hist_min_em 等
            pass
        except Exception:
            pass
        
        return None
    
    def get_valuation_history(self, index_name: str, 
                              force_refresh: bool = False) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        获取指数历史估值数据
        
        Args:
            index_name: 指数名称
            force_refresh: 是否强制刷新
            
        Returns:
            (DataFrame, metadata) 元组
        """
        metadata = {
            "index_name": index_name,
            "source": "unknown",
            "is_realtime": False,
            "update_time": None,
            "warning": None
        }
        
        # 检查缓存
        if not force_refresh and self._is_cache_valid(index_name):
            df = self._load_cache(index_name)
            if df is not None:
                metadata["source"] = "local_cache"
                metadata["is_realtime"] = False
                metadata["update_time"] = datetime.now().isoformat()
                return df, metadata
        
        # 尝试从AKShare获取
        df = self.fetch_from_akshare(index_name)
        if df is not None and not df.empty:
            # 保存到缓存
            self._save_cache(index_name, df, "akshare")
            
            metadata["source"] = "akshare"
            metadata["is_realtime"] = True
            metadata["update_time"] = datetime.now().isoformat()
            return df, metadata
        
        # 尝试加载过期缓存
        df = self._load_cache(index_name)
        if df is not None:
            metadata["source"] = "local_cache_expired"
            metadata["is_realtime"] = False
            metadata["warning"] = "数据可能已过期，请检查更新"
            return df, metadata
        
        # 返回None，调用方需要处理
        metadata["source"] = "none"
        metadata["warning"] = "无法获取数据，请检查网络或数据源"
        return None, metadata
    
    def calculate_percentile(self, current_pe: float, 
                            historical_pe: List[float],
                            method: str = "guorn") -> float:
        """
        计算PE百分位
        
        Args:
            current_pe: 当前PE值
            historical_pe: 历史PE值列表
            method: 计算方法，"guorn"=果仁网方式
            
        Returns:
            百分位值 (0-100)
        """
        if not historical_pe or len(historical_pe) < 2:
            return 50.0
        
        if method == "guorn":
            # 果仁网方式: (当前排名-1) / (总样本数-1) × 100%
            all_values = sorted(historical_pe + [current_pe])
            rank = all_values.index(current_pe) + 1
            percentile = (rank - 1) / (len(all_values) - 1) * 100
        else:
            # 标准百分位
            percentile = (sum(1 for x in historical_pe if x < current_pe) 
                         / len(historical_pe) * 100)
        
        return round(percentile, 2)
    
    def get_current_valuation(self, index_name: str) -> Dict:
        """
        获取指数当前估值和百分位
        
        Args:
            index_name: 指数名称
            
        Returns:
            估值信息字典
        """
        df, metadata = self.get_valuation_history(index_name)
        
        result = {
            "index_name": index_name,
            "pe": None,
            "pe_percentile": None,
            "pb": None,
            "pb_percentile": None,
            "data_source": metadata["source"],
            "is_realtime": metadata["is_realtime"],
            "warning": metadata.get("warning"),
            "update_time": datetime.now().isoformat()
        }
        
        if df is None or df.empty:
            result["warning"] = "【警告：无法获取实时数据】"
            return result
        
        try:
            # 获取当前PE
            current_pe = float(df.iloc[-1].get('pe', df.iloc[-1].get('市盈率', 0)))
            historical_pe = df['pe'].astype(float).tolist() if 'pe' in df.columns else []
            
            if historical_pe:
                historical_pe = historical_pe[:-1]  # 排除当前值
                pe_percentile = self.calculate_percentile(current_pe, historical_pe)
                
                result["pe"] = round(current_pe, 2)
                result["pe_percentile"] = pe_percentile
            
            # 获取PB（如果有）
            if 'pb' in df.columns or '市净率' in df.columns:
                pb_col = 'pb' if 'pb' in df.columns else '市净率'
                current_pb = float(df.iloc[-1].get(pb_col, 0))
                historical_pb = df[pb_col].astype(float).tolist()[:-1]
                
                if historical_pb and current_pb > 0:
                    pb_percentile = self.calculate_percentile(current_pb, historical_pb)
                    result["pb"] = round(current_pb, 2)
                    result["pb_percentile"] = pb_percentile
        except Exception as e:
            result["warning"] = f"数据处理错误: {str(e)}"
        
        return result
    
    def update_all_cache(self) -> Dict:
        """
        更新所有支持指数的缓存
        
        Returns:
            更新结果摘要
        """
        results = {}
        
        for index_name in self.SUPPORTED_INDICES.keys():
            try:
                df, metadata = self.get_valuation_history(index_name, force_refresh=True)
                results[index_name] = {
                    "success": df is not None and not df.empty,
                    "source": metadata["source"],
                    "rows": len(df) if df is not None else 0
                }
            except Exception as e:
                results[index_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results


# 初始化历史PE数据（用于首次运行或测试）
INITIAL_PE_DATA = {
    "沪深300": {
        "历史数据": [
            # 2010-2025年历史PE范围: 8-18
            {"date": "2015-06-12", "pe": 18.5},  # 牛市顶点
            {"date": "2018-12-28", "pe": 10.2},  # 熊市底部
            {"date": "2020-03-23", "pe": 10.8},  # 疫情底部
            {"date": "2021-02-18", "pe": 17.2},  # 阶段高点
            {"date": "2024-01-22", "pe": 10.5},  # 近期低点
        ],
        "百分位参考": {
            "10%": 10.5,
            "30%": 12.0,
            "50%": 13.5,
            "70%": 15.0,
            "90%": 17.0
        }
    }
}


def main():
    """测试数据管理器"""
    print("=" * 60)
    print("估值数据管理器测试")
    print("=" * 60)
    
    manager = ValuationDataManager()
    
    # 测试获取沪深300估值
    print("\n获取沪深300当前估值...")
    result = manager.get_current_valuation("沪深300")
    
    print(f"PE: {result.get('pe')}")
    print(f"PE百分位: {result.get('pe_percentile')}%")
    print(f"数据来源: {result.get('data_source')}")
    print(f"实时数据: {result.get('is_realtime')}")
    
    if result.get("warning"):
        print(f"警告: {result.get('warning')}")
    
    # 更新所有缓存
    print("\n更新所有指数缓存...")
    update_results = manager.update_all_cache()
    for index, info in update_results.items():
        status = "✓" if info.get("success") else "✗"
        print(f"{status} {index}: {info.get('source', info.get('error', 'unknown'))}")


if __name__ == "__main__":
    main()
