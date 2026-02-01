#!/usr/bin/env python3
"""
市场风向标计算模块 - market_indicator.py

用途：计算A股主要指数的PE/PB估值百分位，生成市场风向标数据

数据来源（官方）：
    - 指数PE/PB: 中证指数公司 (csindex.com.cn)
    - 实时行情: 上交所/深交所 (通过AKShare API)
    - 融资融券: 上交所官方披露
    - 北向资金: 港交所披露易

使用示例：
    from market_indicator import MarketIndicator
    
    indicator = MarketIndicator()
    result = indicator.get_market_overview()
    print(result)

依赖：
    pip install akshare pandas numpy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

try:
    from config import get_config
except ImportError:
    # Fallback for running script standalone
    def get_config(section=None):
        configs = {
            "indices": {
                "上证指数": {"code": "000001"}, "沪深300": {"code": "000300"},
                "创业板指": {"code": "399006"}, "中证500": {"code": "000905"},
                "上证50": {"code": "000016"},
            },
            "data_sources": {
                "index_pe": "中证指数公司 (csindex.com.cn)",
                "realtime": "上海证券交易所/深圳证券交易所",
                "margin": "上交所官方披露 (sse.com.cn)",
                "north_flow": "港交所披露易 (hkex.com.hk)",
            }
        }
        if section:
            return configs.get(section, {})
        return configs

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告: 请安装akshare: pip install akshare")

try:
    from valuation_data import ValuationDataManager
    HAS_VALUATION_MANAGER = True
except ImportError:
    HAS_VALUATION_MANAGER = False
    ValuationDataManager = None


class MarketIndicator:
    """
    市场风向标计算器
    
    融合果仁网PE百分位计算方法：
    PE百分位 = (当前PE排名 - 1) / (历史样本数 - 1) × 100%
    """
    
    def __init__(self):
        self.cache = {}
        self.update_time = datetime.now()
        self._valuation_manager = ValuationDataManager() if HAS_VALUATION_MANAGER else None
        self._data_warnings = []  # 收集数据警告

        # 从配置加载
        self.indices_config = get_config("indices")
        self.data_sources_config = get_config("data_sources")
        
        self.INDEX_CODES = {name: details["code"] for name, details in self.indices_config.items()}
        self.DATA_SOURCES = self.data_sources_config
    
    def calculate_percentile(self, current_value: float, 
                            historical_values: List[float]) -> float:
        """
        计算PE/PB百分位（果仁网方式）
        """
        if not historical_values or len(historical_values) < 2:
            return 50.0
        
        all_values = sorted(historical_values + [current_value])
        rank = all_values.index(current_value) + 1
        percentile = (rank - 1) / (len(all_values) - 1) * 100
        
        return round(percentile, 2)
    
    def get_valuation_status(self, percentile: float) -> Dict[str, str]:
        """
        根据百分位判断估值状态
        """
        if percentile < 20:
            return {"status": "低估", "emoji": "🟢", "signal": "积极买入", "color": "#22c55e"}
        elif percentile < 40:
            return {"status": "偏低估", "emoji": "🟡", "signal": "可以买入", "color": "#84cc16"}
        elif percentile < 60:
            return {"status": "合理", "emoji": "🟡", "signal": "持有观望", "color": "#eab308"}
        elif percentile < 80:
            return {"status": "偏高估", "emoji": "🟠", "signal": "考虑减仓", "color": "#f97316"}
        else:
            return {"status": "高估", "emoji": "🔴", "signal": "准备卖出", "color": "#ef4444"}
    
    def get_index_valuation(self, index_name: str, years: int = 10) -> Dict[str, Any]:
        """
        获取指数估值数据 - 使用中证指数官方数据
        
        数据源: stock_zh_index_value_csindex (中证指数公司)
        """
        index_code = self.INDEX_CODES.get(index_name)
        if not index_code:
            return {"error": f"未知指数: {index_name}"}
        
        # 尝试使用AKShare获取中证指数估值
        if HAS_AKSHARE:
            try:
                # 使用正确的API: stock_zh_index_value_csindex
                df = ak.stock_zh_index_value_csindex(symbol=index_code)
                if df is not None and not df.empty:
                    # 获取最新数据
                    latest = df.iloc[-1]
                    current_pe = float(latest['市盈率1'])  # 市盈率1是主要PE
                    
                    # 获取历史PE用于计算百分位
                    historical_pe = df['市盈率1'].astype(float).tolist()[:-1]
                    if len(historical_pe) >= 10:
                        pe_percentile = self.calculate_percentile(current_pe, historical_pe)
                    else:
                        # 数据不足时使用默认估算
                        pe_percentile = 50.0
                    
                    status_info = self.get_valuation_status(pe_percentile)
                    
                    return {
                        "index_name": index_name,
                        "index_code": index_code,
                        "pe": round(current_pe, 2),
                        "pe_percentile": round(pe_percentile, 2),
                        "dividend_yield": round(float(latest.get('股息率1', 0)), 2),
                        **status_info,
                        "data_source": "中证指数公司 (csindex.com.cn)",
                        "data_date": str(latest['日期']),
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "is_real_data": True
                    }
            except Exception as e:
                self._data_warnings.append(f"{index_name}: AKShare失败 - {str(e)[:50]}")
        
        # 备用: ValuationDataManager
        if self._valuation_manager:
            try:
                result = self._valuation_manager.get_current_valuation(index_name)
                if result.get("pe") and result.get("pe_percentile") is not None:
                    status_info = self.get_valuation_status(result["pe_percentile"])
                    return {**result, **status_info, "index_code": index_code}
            except Exception as e:
                self._data_warnings.append(f"{index_name}: Cache失败 - {str(e)[:30]}")
        
        self._data_warnings.append(f"{index_name}: 【警告】使用静态模拟数据")
        return self._get_mock_valuation(index_name)
    
    def _get_mock_valuation(self, index_name: str) -> Dict[str, Any]:
        """返回基于公开数据的估值信息"""
        mock_data = {
            "沪深300": {"pe": 14.31, "pe_percentile": 14.40},
            "上证指数": {"pe": 16.90, "pe_percentile": 25.00},
            "创业板指": {"pe": 52.87, "pe_percentile": 38.75},
            "中证500": {"pe": 25.50, "pe_percentile": 35.00},
            "上证50": {"pe": 11.50, "pe_percentile": 18.00},
        }
        data = mock_data.get(index_name, {"pe": 15.00, "pe_percentile": 50.00})
        status_info = self.get_valuation_status(data["pe_percentile"])
        
        return {
            "index_name": index_name, "index_code": self.INDEX_CODES.get(index_name, ""),
            "pe": data["pe"], "pe_percentile": data["pe_percentile"], **status_info,
            "data_source": "公开模拟数据", "is_real_data": False,
            "note": "此为静态模拟数据，非实时"
        }
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """获取市场情绪数据"""
        result = {"data_sources": {}}
        if not HAS_AKSHARE: return self._get_mock_sentiment()
        
        try:
            margin_df = ak.stock_margin_sse()
            if not margin_df.empty:
                latest = margin_df.iloc[0]
                result["margin_balance"] = {"value": float(latest.get("融资余额(元)", 0)) / 1e8, "unit": "亿元", "date": str(latest.get("信用交易日期", ""))}
                result["data_sources"]["margin"] = self.DATA_SOURCES["margin"]
        except Exception: pass
        
        try:
            north_df = ak.stock_hsgt_north_net_flow_in_em()
            if not north_df.empty:
                total_flow = north_df.head(5)['净流入'].astype(float).sum() / 1e8
                result["north_flow_5d"] = {"value": round(total_flow, 2), "unit": "亿元", "period": "近5个交易日"}
                result["data_sources"]["north_flow"] = self.DATA_SOURCES["north_flow"]
        except Exception: pass
        
        try:
            spot_df = ak.stock_zh_a_spot_em()
            up = len(spot_df[spot_df['涨跌幅'].astype(float) > 0])
            down = len(spot_df[spot_df['涨跌幅'].astype(float) < 0])
            result["advance_decline_ratio"] = {"up_count": up, "down_count": down, "ratio": round(up / max(down, 1), 2)}
            result["data_sources"]["realtime"] = self.DATA_SOURCES["realtime"]
        except Exception: pass
        
        return result if "margin_balance" in result else self._get_mock_sentiment()

    def _get_mock_sentiment(self) -> Dict[str, Any]:
        """返回基于公开数据的情绪指标"""
        return {"note": "情绪指标为模拟数据"}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """获取完整的市场风向标概览"""
        from data_fetcher import DataFetcher
        
        self._data_warnings = []
        overview = {
            "title": "市场风向标",
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indices": [],
            "risk_free_rate": 2.3, # 默认值
            "erp": 0.0,
            "sentiment": None,
            "data_sources": list(self.DATA_SOURCES.values()),
            "warnings": []
        }
        
        # 获取无风险利率 (10年期国债收益率)
        try:
            fetcher = DataFetcher()
            if hasattr(fetcher, 'get_treasury_yield'):
                overview["risk_free_rate"] = fetcher.get_treasury_yield(country="CN")
        except Exception as e:
            self._data_warnings.append(f"获取无风险利率失败: {e}")

        # 从配置中获取要展示的指数列表
        main_indices = list(self.INDEX_CODES.keys())
        avg_pe = 0
        valid_count = 0
        
        for index_name in main_indices:
            idx_data = self.get_index_valuation(index_name)
            overview["indices"].append(idx_data)
            if idx_data.get("pe"):
                avg_pe += idx_data["pe"]
                valid_count += 1
                
        # 计算市场整体ERP (1/平均PE - 无风险利率)
        if valid_count > 0:
            market_pe = avg_pe / valid_count
            # ERP = E/P - Rf
            overview["erp"] = round((100 / market_pe) - overview["risk_free_rate"], 2)
        
        overview["sentiment"] = self.get_market_sentiment()
        overview["strategy"] = self._generate_strategy(overview)
        
        if self._data_warnings:
            overview["warnings"] = self._data_warnings
            if len([w for w in self._data_warnings if "模拟数据" in w]) == len(main_indices):
                overview["data_warning"] = "【重要警告】当前为静态模拟数据，结果仅供参考"
        
        return overview
    
    def _generate_strategy(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """生成投资策略建议"""
        percentiles = [idx.get("pe_percentile", 50) for idx in overview.get("indices", []) if isinstance(idx, dict)]
        avg_percentile = sum(percentiles) / len(percentiles) if percentiles else 50
        
        if avg_percentile < 25: position, strategy, risk = "70-80%", "积极配置", "低"
        elif avg_percentile < 40: position, strategy, risk = "60-70%", "逐步建仓", "中低"
        elif avg_percentile < 60: position, strategy, risk = "50-60%", "持有观望", "中"
        elif avg_percentile < 75: position, strategy, risk = "30-50%", "逐步减仓", "中高"
        else: position, strategy, risk = "10-30%", "防守为主", "高"
        
        return {
            "avg_percentile": round(avg_percentile, 2),
            "recommended_position": position, "strategy": strategy, "risk_level": risk,
            "master_views": {
                "buffett": self._get_buffett_view(avg_percentile),
                "howard_marks": self._get_marks_view(avg_percentile),
                "duan_yongping": self._get_duan_view(avg_percentile)
            }
        }
    
    def _get_buffett_view(self, p: float) -> str:
        if p < 30: return "当前市场处于历史低估区域，符合'安全边际'原则。是'别人恐惧我贪婪'的时刻，是长期投资者难得的买入机会。"
        if p < 50: return "市场估值相对合理偏低，具有一定安全边际。可以寻找优质企业逐步建仓，但要确保在自己的能力圈内投资。"
        if p < 70: return "市场估值处于中性水平，需要更加精挑细选。关注那些具有持久竞争优势的企业，不要因为市场氛围而冲动买入。"
        return "市场估值偏高，安全边际不足。是'别人贪婪我恐惧'的时刻，应该保持谨慎，可以考虑逐步减仓锁定收益。"

    def _get_marks_view(self, p: float) -> str:
        if p < 30: return "市场周期处于底部区域，悲观情绪蔓延。记住：周期的极端不会永远持续。现在正是逆向投资的好时机，但要有耐心。"
        if p < 50: return "市场逐渐走出悲观，但还未进入狂热。这是周期上行的初期阶段，可以保持适度乐观，但不要忘记风险管理。"
        if p < 70: return "市场情绪趋于中性偏乐观。需要保持二层思维：大家都看好的东西可能已经price in。关注那些被市场忽视的机会。"
        return "市场接近周期顶部，乐观情绪高涨。历史告诉我们，繁荣之后必有调整。现在应该更加谨慎，控制仓位。"

    def _get_duan_view(self, p: float) -> str:
        if p < 30: return "市场给出了好价格。但记住'三好'原则：不仅要价格好，生意和管理层也要好。不懂不做，即使价格便宜也要谨慎。"
        if p < 50: return "市场估值合理偏低。可以寻找那些'好生意+好管理层'的公司，如果价格合适就可以考虑买入。做对的事情，把事情做对。"
        if p < 70: return "市场估值中性。此时更需要专注于公司本身，而非市场涨跌。本分做事，不要因为市场上涨就降低选股标准。"
        return "市场整体偏贵。好公司的好价格难觅，宁可错过也不要盲目追高。保持耐心，做长期主义者。"
    
    def to_json(self) -> str:
        return json.dumps(self.get_market_overview(), ensure_ascii=False, indent=2)


def main():
    """主函数 - 支持命令行参数"""
    parser = argparse.ArgumentParser(description="获取市场风向标或指定指数的估值")
    indicator = MarketIndicator()
    
    parser.add_argument(
        "--index",
        nargs='+',
        type=str,
        help=f"指定一个或多个指数名称以获取其详细估值. 支持的指数: {', '.join(indicator.INDEX_CODES.keys())}"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以JSON格式输出完整的市场概览"
    )
    
    args = parser.parse_args()
    
    if args.index:
        print("【指定指数估值详情】")
        for index_name in args.index:
            if index_name not in indicator.INDEX_CODES:
                print(f"\n错误: 不支持的指数 '{index_name}'。请从支持列表中选择。")
                continue
            
            valuation = indicator.get_index_valuation(index_name)
            print("-" * 40)
            print(f"指数名称: {valuation.get('index_name', 'N/A')}")
            print(f"  - PE: {valuation.get('pe', 'N/A')}")
            print(f"  - PE百分位: {valuation.get('pe_percentile', 'N/A')}% ")
            print(f"  - 状态: {valuation.get('emoji', '')} {valuation.get('status', 'N/A')}")
            print(f"  - 信号: {valuation.get('signal', 'N/A')}")
            print(f"  - 数据来源: {valuation.get('data_source', 'N/A')}")
            if valuation.get('warning'):
                print(f"  - 警告: {valuation.get('warning')}")

    elif args.json:
        print(indicator.to_json())
        
    else:
        overview = indicator.get_market_overview()
        print("=" * 60, "\n市场风向标\n", "=" * 60, f"\n更新时间: {overview['update_time']}\n")
        
        if overview.get("data_warning"):
            print(f"|| {overview['data_warning']} ||\n")

        print("【主要指数估值】\n" + "-" * 60)
        for idx in overview.get('indices', []):
            print(f"{idx.get('index_name','N/A'):8} | PE: {idx.get('pe', 0):6.2f} | "
                  f"百分位: {idx.get('pe_percentile', 0):5.2f}% | {idx.get('emoji','')}{idx.get('status','')}")
        
        strategy = overview.get('strategy', {})
        print("\n【投资策略建议】\n" + "-" * 60)
        print(f"综合估值: {strategy.get('avg_percentile')}% | 建议仓位: {strategy.get('recommended_position')} | 策略方向: {strategy.get('strategy')}")
        
        master_views = strategy.get('master_views', {})
        print("\n【大师视角】\n" + "-" * 60)
        print(f"🎯 巴菲特: {master_views.get('buffett')}")
        print(f"\n📊 Howard Marks: {master_views.get('howard_marks')}")
        print(f"\n💡 段永平: {master_views.get('duan_yongping')}")
        
        print("\n【数据来源】\n" + "-" * 60)
        for source in overview.get('data_sources', []): print(f"  • {source}")
        if overview.get("warnings"): print("\n【警告】\n" + "-" * 60 + "\n" + "\n".join(overview["warnings"]))

if __name__ == "__main__":
    import argparse
    main()
