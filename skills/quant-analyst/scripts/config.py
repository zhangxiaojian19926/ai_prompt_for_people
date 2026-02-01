#!/usr/bin/env python3
"""
quant-analyst 中央配置文件

所有可调参数集中管理，脚本从此处读取配置
"""

# ============ 技术指标参数 ============

MA_PERIODS = {
    "short": 5,
    "medium": 10,
    "long": 20,
    "trend": 60,
    "super_long": 120
}

MACD_PARAMS = {
    "fast": 12,
    "slow": 26,
    "signal": 9
}

RSI_PARAMS = {
    "period": 14,
    "oversold": 30,
    "overbought": 70
}

BOLLINGER_PARAMS = {
    "period": 20,
    "std_dev": 2
}

# ============ 估值策略参数 ============

VALUATION_THRESHOLDS = {
    "very_undervalued": 20,    # PE百分位 < 20%
    "undervalued": 40,         # PE百分位 < 40%
    "fairly_valued": 60,       # PE百分位 < 60%
    "overvalued": 80,          # PE百分位 < 80%
    "very_overvalued": 100     # PE百分位 >= 80%
}

# 估值策略买卖阈值
VALUE_STRATEGY = {
    "buy_threshold": 20,       # PE百分位 < 20% 买入
    "sell_threshold": 70       # PE百分位 > 70% 卖出
}

# ============ 交易成本 ============

TRADING_COSTS = {
    "commission": 0.0003,      # 佣金率 0.03%
    "stamp_duty": 0.001,       # 印花税 0.1% (仅卖出)
    "slippage": 0.001          # 滑点 0.1%
}

# ============ 回测参数 ============

BACKTEST_PARAMS = {
    "initial_capital": 100000,   # 初始资金
    "risk_free_rate": 0.03,      # 无风险利率 3%
    "warmup_period": 60          # 预热期（天）
}

# ============ 仓位管理 ============

POSITION_PARAMS = {
    # 根据PE百分位的建议仓位
    "percentile_0_25": {"min": 0.7, "max": 0.8},    # 低估
    "percentile_25_40": {"min": 0.6, "max": 0.7},   # 偏低估
    "percentile_40_60": {"min": 0.5, "max": 0.6},   # 合理
    "percentile_60_75": {"min": 0.3, "max": 0.5},   # 偏高估
    "percentile_75_100": {"min": 0.1, "max": 0.3}   # 高估
}

# ============ 情绪指标参数 ============

SENTIMENT_PARAMS = {
    "margin_change": {"min": -5, "max": 5},         # 融资余额变化%
    "turnover_rate": {"min": 0.5, "max": 3},        # 换手率
    "advance_decline": {"min": 0.3, "max": 3},      # 涨跌比
    "volume_ratio": {"min": 0.5, "max": 2},         # 成交量比
    "north_flow": {"min": -100, "max": 100}         # 北向资金(亿)
}

# ============ 数据源配置 ============

DATA_SOURCES = {
    "index_pe": "中证指数公司 (csindex.com.cn)",
    "realtime": "上海证券交易所/深圳证券交易所",
    "margin": "上交所官方披露 (sse.com.cn)",
    "north_flow": "港交所披露易 (hkex.com.hk)"
}

# 缓存配置
CACHE_CONFIG = {
    "valuation_expiry_days": 1,    # 估值缓存过期天数
    "cache_dir": "data/valuation_cache"
}

# ============ 支持的指数 ============
# 注意: 仅包含中证指数公司支持的指数代码
# 深交所指数(如创业板指399006)需要使用其他API

SUPPORTED_INDICES = {
    "沪深300": {"code": "000300", "name_en": "CSI300"},
    "上证指数": {"code": "000001", "name_en": "SSE"},
    "中证500": {"code": "000905", "name_en": "CSI500"},
    "中证1000": {"code": "000852", "name_en": "CSI1000"},
    "上证50": {"code": "000016", "name_en": "SSE50"},
    "中证100": {"code": "000903", "name_en": "CSI100"},  # 替代创业板指
    "科创50": {"code": "000688", "name_en": "STAR50"},
}


def get_config(section: str = None):
    """
    获取配置
    
    Args:
        section: 配置节名称，None返回全部
        
    Returns:
        配置字典
    """
    all_config = {
        "ma": MA_PERIODS,
        "macd": MACD_PARAMS,
        "rsi": RSI_PARAMS,
        "bollinger": BOLLINGER_PARAMS,
        "valuation": VALUATION_THRESHOLDS,
        "value_strategy": VALUE_STRATEGY,
        "trading_costs": TRADING_COSTS,
        "backtest": BACKTEST_PARAMS,
        "position": POSITION_PARAMS,
        "sentiment": SENTIMENT_PARAMS,
        "data_sources": DATA_SOURCES,
        "cache": CACHE_CONFIG,
        "indices": SUPPORTED_INDICES
    }
    
    if section:
        return all_config.get(section, {})
    return all_config


if __name__ == "__main__":
    import json
    print("quant-analyst 配置:")
    print(json.dumps(get_config(), ensure_ascii=False, indent=2))
