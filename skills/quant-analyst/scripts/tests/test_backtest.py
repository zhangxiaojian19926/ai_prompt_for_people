#!/usr/bin/env python3
"""
回测系统单元测试 - test_backtest.py
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
from unittest.mock import patch

scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, scripts_dir)

from backtest import Backtester, Trade, Signal

class TestBacktester(unittest.TestCase):

    def setUp(self):
        """设置测试所需的通用参数"""
        self.start_date = "2024-01-01"
        self.end_date = "2024-02-01"
        self.symbol = "TEST"

    def test_calculate_metrics(self):
        """测试核心业绩指标计算的准确性"""
        with patch.object(Backtester, '_load_data', return_value=None):
            bt = Backtester(symbol=self.symbol, start_date=self.start_date, end_date=self.end_date)

        # 1. 手动准备数据
        bt.trades = [
            Trade(date="2024-01-10", signal=Signal.BUY, price=100.0, shares=1000, value=100000, reason=""),
            Trade(date="2024-01-12", signal=Signal.SELL, price=120.0, shares=1000, value=120000, reason=""),
        ]
        bt.equity_curve = pd.DataFrame({'equity': [100000, 110000, 120000]})

        # 2. 执行计算
        results = bt._calculate_metrics()

        # 3. 验证结果
        self.assertAlmostEqual(results.total_return, 20.0, places=2)
        # 胜率: 因简化后的交易列表不完整，暂不测试胜率和盈亏比
        
        # 测试最大回撤
        bt.equity_curve = pd.DataFrame({'equity': [100, 120, 110, 130]})
        results_dd = bt._calculate_metrics()
        self.assertAlmostEqual(results_dd.max_drawdown, 8.33, places=2)

    def test_get_target_position_by_percentile(self):
        """测试根据PE百分位获取目标仓位的逻辑"""
        with patch.object(Backtester, '_load_data', return_value=None):
            bt = Backtester(symbol=self.symbol, start_date=self.start_date, end_date=self.end_date)
        
        # 极度低估
        pos = bt._get_target_position_by_percentile(15)
        self.assertEqual(pos, bt.position_config["percentile_0_25"]["max"])
        
        # 偏低估
        pos = bt._get_target_position_by_percentile(30)
        self.assertEqual(pos, bt.position_config["percentile_25_40"]["max"])
        
        # 合理
        pos = bt._get_target_position_by_percentile(50)
        self.assertEqual(pos, bt.position_config["percentile_40_60"]["max"])

        # 偏高估
        pos = bt._get_target_position_by_percentile(70)
        self.assertEqual(pos, bt.position_config["percentile_60_75"]["min"])

        # 极度高估
        pos = bt._get_target_position_by_percentile(90)
        self.assertEqual(pos, bt.position_config["percentile_75_100"]["min"])

def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBacktester))
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    main()
