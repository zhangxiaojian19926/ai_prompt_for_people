#!/usr/bin/env python3
"""
市场风向标单元测试
"""

import sys
import os

# 添加scripts目录到路径
scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, scripts_dir)

from market_indicator import MarketIndicator


def test_calculate_percentile():
    """测试PE百分位计算（果仁网方式）"""
    indicator = MarketIndicator()
    
    # 果仁网方式: (当前排名-1) / (总样本数-1) × 100%
    # 历史数据 [10, 20, 30, 40]，当前值加入后排序
    
    # 测试用例1：当前值最小
    # 历史 [10, 20, 30, 40] + 当前值 5 → 排序 [5, 10, 20, 30, 40]
    # 排名=1, (1-1)/(5-1) = 0%
    result = indicator.calculate_percentile(5, [10, 20, 30, 40])
    assert result == 0.0, f"最小值应为0%, 实际: {result}%"
    
    # 测试用例2：当前值最大
    # 历史 [10, 20, 30, 40] + 当前值 50 → 排序 [10, 20, 30, 40, 50]
    # 排名=5, (5-1)/(5-1) = 100%
    result = indicator.calculate_percentile(50, [10, 20, 30, 40])
    assert result == 100.0, f"最大值应为100%, 实际: {result}%"
    
    # 测试用例3：当前值在中间
    # 历史 [10, 20, 40, 50] + 当前值 30 → 排序 [10, 20, 30, 40, 50]
    # 排名=3, (3-1)/(5-1) = 50%
    result = indicator.calculate_percentile(30, [10, 20, 40, 50])
    assert result == 50.0, f"中间值应为50%, 实际: {result}%"
    
    print("✓ test_calculate_percentile 通过")


def test_get_valuation_status():
    """测试估值状态判断"""
    indicator = MarketIndicator()
    
    # 低估区域 (<20%)
    status = indicator.get_valuation_status(15)
    assert status["status"] == "低估", f"15%应为低估, 实际: {status['status']}"
    assert status["emoji"] == "🟢"
    
    # 偏低估 (20-40%)
    status = indicator.get_valuation_status(30)
    assert status["status"] == "偏低估", f"30%应为偏低估, 实际: {status['status']}"
    
    # 合理 (40-60%)
    status = indicator.get_valuation_status(50)
    assert status["status"] == "合理", f"50%应为合理, 实际: {status['status']}"
    
    # 偏高估 (60-80%)
    status = indicator.get_valuation_status(70)
    assert status["status"] == "偏高估", f"70%应为偏高估, 实际: {status['status']}"
    
    # 高估 (>80%)
    status = indicator.get_valuation_status(85)
    assert status["status"] == "高估", f"85%应为高估, 实际: {status['status']}"
    assert status["emoji"] == "🔴"
    
    print("✓ test_get_valuation_status 通过")


def test_get_index_valuation():
    """测试指数估值获取"""
    indicator = MarketIndicator()
    
    # 测试沪深300
    valuation = indicator.get_index_valuation("沪深300")
    assert "pe" in valuation, "应包含PE值"
    assert "pe_percentile" in valuation, "应包含PE百分位"
    assert "status" in valuation, "应包含状态"
    assert "data_source" in valuation or "data_sources" in valuation, "应包含数据来源"
    
    print(f"  沪深300 PE: {valuation['pe']}, 百分位: {valuation['pe_percentile']}%")
    print("✓ test_get_index_valuation 通过")


def test_get_market_overview():
    """测试市场概览获取"""
    indicator = MarketIndicator()
    
    overview = indicator.get_market_overview()
    
    assert "indices" in overview, "应包含indices"
    assert "strategy" in overview, "应包含strategy"
    assert "data_sources" in overview, "应包含data_sources"
    assert len(overview["indices"]) >= 3, "应至少包含3个指数"
    
    print(f"  包含 {len(overview['indices'])} 个指数")
    print("✓ test_get_market_overview 通过")


def test_strategy_generation():
    """测试策略生成"""
    indicator = MarketIndicator()
    overview = indicator.get_market_overview()
    
    strategy = overview.get("strategy", {})
    
    assert "avg_percentile" in strategy, "应包含平均百分位"
    assert "recommended_position" in strategy, "应包含建议仓位"
    assert "master_views" in strategy, "应包含大师视角"
    
    master_views = strategy.get("master_views", {})
    assert "buffett" in master_views, "应包含巴菲特视角"
    assert "howard_marks" in master_views, "应包含Howard Marks视角"
    assert "duan_yongping" in master_views, "应包含段永平视角"
    
    print(f"  综合估值: {strategy.get('avg_percentile')}%")
    print(f"  建议仓位: {strategy.get('recommended_position')}")
    print("✓ test_strategy_generation 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行 market_indicator 单元测试")
    print("=" * 60)
    print()
    
    tests = [
        test_calculate_percentile,
        test_get_valuation_status,
        test_get_index_valuation,
        test_get_market_overview,
        test_strategy_generation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 错误: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
