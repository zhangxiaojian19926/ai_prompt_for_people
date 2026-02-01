#!/usr/bin/env python3
"""
估值数据管理模块单元测试
"""

import unittest
import os
import sys
import pandas as pd
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add scripts directory to path to allow import of valuation_data
scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, scripts_dir)

from valuation_data import ValuationDataManager

# A mock dataframe that looks like the output of ak.index_value_hist_funddb
MOCK_AKSHARE_DF = pd.DataFrame({
    "日期": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    "市盈率": [10.0, 11.0, 10.5],
})

class TestValuationDataManager(unittest.TestCase):
    
    def setUp(self):
        """为每个测试设置一个临时的缓存目录"""
        self.test_cache_dir = os.path.join(scripts_dir, "tests", "temp_cache")
        if not os.path.exists(self.test_cache_dir):
            os.makedirs(self.test_cache_dir)
        self.manager = ValuationDataManager(cache_dir=self.test_cache_dir)
        self.index_name = "沪深300"

    def tearDown(self):
        """在每个测试后清理临时缓存目录"""
        for f in os.listdir(self.test_cache_dir):
            os.remove(os.path.join(self.test_cache_dir, f))
        os.rmdir(self.test_cache_dir)

    def test_01_fetch_and_cache(self):
        """测试：第一次获取数据时，应调用API并创建缓存文件"""
        with patch('valuation_data.ak.index_value_hist_funddb') as mock_ak_call:
            mock_ak_call.return_value = MOCK_AKSHARE_DF
            
            df, metadata = self.manager.get_valuation_history(self.index_name)
            
            mock_ak_call.assert_called_once()
            self.assertIsNotNone(df)
            self.assertEqual(len(df), 3)
            self.assertEqual(metadata["source"], "akshare")
            
            cache_path = self.manager._get_cache_path(self.index_name)
            meta_path = self.manager._get_meta_path(self.index_name)
            self.assertTrue(os.path.exists(cache_path))
            self.assertTrue(os.path.exists(meta_path))
            
            with open(meta_path, 'r') as f:
                meta_content = json.load(f)
            self.assertEqual(meta_content["source"], "akshare")

    def test_02_load_from_valid_cache(self):
        """测试：当存在有效缓存时，不应调用API，而是从缓存读取"""
        self.manager._save_cache(self.index_name, MOCK_AKSHARE_DF, "akshare")
        
        with patch('valuation_data.ak.index_value_hist_funddb') as mock_ak_call:
            df, metadata = self.manager.get_valuation_history(self.index_name)
            
            mock_ak_call.assert_not_called()
            self.assertIsNotNone(df)
            self.assertEqual(len(df), 3)
            self.assertEqual(metadata["source"], "local_cache")

    def test_03_cache_expiry_and_refresh(self):
        """测试：当缓存过期时，应重新调用API并更新缓存"""
        expired_date = (datetime.now() - timedelta(days=self.manager.CACHE_EXPIRY_DAYS + 1)).isoformat()
        meta_path = self.manager._get_meta_path(self.index_name)
        with open(meta_path, 'w') as f:
            json.dump({"last_update": expired_date, "source": "expired"}, f)
        MOCK_AKSHARE_DF.to_csv(self.manager._get_cache_path(self.index_name), index=False)
        
        new_df = pd.DataFrame({"日期": pd.to_datetime(["2025-01-01"]), "市盈率": [15.0]})
        
        with patch('valuation_data.ak.index_value_hist_funddb') as mock_ak_call:
            mock_ak_call.return_value = new_df
            df, metadata = self.manager.get_valuation_history(self.index_name)

            mock_ak_call.assert_called_once()
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["市盈率"], 15.0)
            self.assertEqual(metadata["source"], "akshare")

    def test_04_api_failure_fallback(self):
        """测试：当API调用失败时，应尝试加载（即使是过期的）缓存"""
        self.manager._save_cache(self.index_name, MOCK_AKSHARE_DF, "akshare")
        expired_date = (datetime.now() - timedelta(days=3)).isoformat()
        with open(self.manager._get_meta_path(self.index_name), 'w') as f:
             json.dump({"last_update": expired_date}, f)

        with patch('valuation_data.ak.index_value_hist_funddb') as mock_ak_call:
            mock_ak_call.side_effect = Exception("API call failed")
            df, metadata = self.manager.get_valuation_history(self.index_name)
            
            self.assertIsNotNone(df)
            self.assertEqual(len(df), 3)
            self.assertEqual(metadata["source"], "local_cache_expired")
            self.assertIn("过期", metadata.get("warning", ""))

    def test_05_calculate_percentile(self):
        """测试百分位计算逻辑"""
        manager = self.manager
        hist = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        self.assertAlmostEqual(manager.calculate_percentile(55, hist), 50.0)
        self.assertAlmostEqual(manager.calculate_percentile(1, hist), 0.0)
        self.assertAlmostEqual(manager.calculate_percentile(110, hist), 100.0)
        self.assertAlmostEqual(manager.calculate_percentile(50, hist), 40.0)
        self.assertAlmostEqual(manager.calculate_percentile(50, []), 50.0)

def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestValuationDataManager))
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    main()
