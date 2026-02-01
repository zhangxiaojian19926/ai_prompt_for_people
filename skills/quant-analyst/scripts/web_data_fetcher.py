#!/usr/bin/env python3
"""
浏览器数据获取模块 - web_data_fetcher.py

通过浏览器MCP获取实时行情数据，作为AKShare的补充和验证数据源。

使用场景:
    - AKShare数据获取失败时的备用方案
    - 验证AKShare数据的准确性
    - 获取实时盘中数据

数据源:
    - 东方财富: https://quote.eastmoney.com/
    - 同花顺: https://stockpage.10jqka.com.cn/
    - 新浪财经: https://finance.sina.com.cn/

注意: 此模块需要在支持浏览器MCP的Agent环境中使用
"""

from typing import Dict, Any, Optional
from datetime import datetime
import re


class WebDataFetcher:
    """
    浏览器数据获取器
    
    在Agent环境中，通过浏览器工具获取实时行情数据
    """
    
    # 数据源URL模板
    DATA_SOURCES = {
        "eastmoney": {
            "etf": "https://quote.eastmoney.com/sz{code}.html",
            "stock_sh": "https://quote.eastmoney.com/sh{code}.html",
            "stock_sz": "https://quote.eastmoney.com/sz{code}.html",
            "name": "东方财富"
        },
        "sina": {
            "etf": "https://finance.sina.com.cn/fund/quotes/{code}/bc.shtml",
            "stock": "https://finance.sina.com.cn/realstock/company/{market}{code}/nc.shtml",
            "name": "新浪财经"
        }
    }
    
    def __init__(self):
        self.last_fetch_time = None
        self.cached_data = {}
    
    @staticmethod
    def get_market_code(symbol: str) -> str:
        """
        根据证券代码判断市场
        
        Args:
            symbol: 证券代码（纯数字,如'600519','159928'）
            
        Returns:
            市场代码: 'sh'(上海) 或 'sz'(深圳)
            
        规则:
            - 6开头: 上海主板 (sh)
            - 000开头: 深圳主板 (sz)
            - 002开头: 中小板 (sz)
            - 003开头: 深圳主板 (sz)
            - 300开头: 创业板 (sz)
            - 688开头: 科创板 (sh)
            - 51/52/56/58开头: 上海ETF (sh)
            - 15/16开头: 深圳ETF (sz)
        """
        if symbol.startswith('6'):
            return 'sh'
        elif symbol.startswith(('51', '52', '56', '58')):
            return 'sh'
        elif symbol.startswith('688'):
            return 'sh'
        else:
            return 'sz'
    
    def get_url_for_symbol(self, symbol: str, source: str = "eastmoney") -> str:
        """
        根据股票/ETF代码生成对应的行情URL
        
        Args:
            symbol: 股票/ETF代码，如 '159928', '600519'
            source: 数据源，默认eastmoney
            
        Returns:
            行情页面URL
        """
        source_config = self.DATA_SOURCES.get(source, self.DATA_SOURCES["eastmoney"])
        market = self.get_market_code(symbol)
        
        # 生成URL
        if market == 'sh':
            template = source_config.get("stock_sh", source_config.get("etf"))
            return f"https://quote.eastmoney.com/sh{symbol}.html"
        else:
            template = source_config.get("stock_sz", source_config.get("etf"))
            return f"https://quote.eastmoney.com/sz{symbol}.html"
    
    def parse_eastmoney_data(self, dom_text: str) -> Dict[str, Any]:
        """
        解析东方财富网页DOM获取行情数据
        
        Args:
            dom_text: 网页DOM文本内容
            
        Returns:
            包含价格、涨跌幅等信息的字典
        """
        result = {
            "source": "东方财富",
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_realtime": True
        }
        
        # 提取价格 (通常在class包含"price"的元素中)
        price_patterns = [
            r'最新[：:]\s*([\d.]+)',
            r'现价[：:]\s*([\d.]+)',
            r'class="price[^"]*"[^>]*>([\d.]+)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, dom_text)
            if match:
                result["price"] = float(match.group(1))
                break
        
        # 提取涨跌幅
        change_patterns = [
            r'涨跌幅[：:]\s*([-+]?[\d.]+)%',
            r'change[^"]*"[^>]*>([-+]?[\d.]+)%',
        ]
        for pattern in change_patterns:
            match = re.search(pattern, dom_text)
            if match:
                result["change_pct"] = float(match.group(1))
                break
        
        # 提取成交额
        amount_patterns = [
            r'成交额[：:]\s*([\d.]+)\s*(亿|万)',
            r'amount[^"]*"[^>]*>([\d.]+)\s*(亿|万)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, dom_text)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                if unit == "亿":
                    result["amount"] = value * 1e8
                elif unit == "万":
                    result["amount"] = value * 1e4
                break
        
        return result
    
    def generate_browser_prompt(self, symbol: str, source: str = "eastmoney") -> str:
        """
        生成浏览器Agent的提示词
        
        用于指导浏览器Agent获取特定股票的行情数据
        
        Args:
            symbol: 股票/ETF代码
            source: 数据源
            
        Returns:
            用于browser_subagent的Task描述
        """
        url = self.get_url_for_symbol(symbol, source)
        source_name = self.DATA_SOURCES.get(source, {}).get("name", source)
        
        prompt = f"""访问{source_name}网站获取股票/ETF {symbol} 的最新价格信息。

步骤：
1. 打开 {url}
2. 等待页面加载完成
3. 找到并记录以下信息：
   - 最新价格
   - 涨跌幅
   - 涨跌额
   - 最新日期/时间
   - 成交额
   - 今开盘/最高/最低/昨收
4. 返回获取到的所有数据，格式如下：
   price: xxx
   change_pct: xxx%
   date: xxxx-xx-xx
   amount: xxx亿

请返回你找到的所有价格相关信息。"""
        
        return prompt
    
    def validate_against_akshare(self, web_data: Dict, akshare_data: Dict) -> Dict[str, Any]:
        """
        将浏览器获取的数据与AKShare数据进行对比验证
        
        Args:
            web_data: 浏览器获取的数据
            akshare_data: AKShare获取的数据
            
        Returns:
            验证结果，包含是否一致、差异等信息
        """
        result = {
            "is_consistent": True,
            "differences": [],
            "recommended_data": {},
            "validation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 对比价格
        web_price = web_data.get("price")
        ak_price = akshare_data.get("close") or akshare_data.get("price")
        
        if web_price and ak_price:
            price_diff = abs(web_price - ak_price)
            if price_diff > 0.001:  # 允许0.001的误差
                result["is_consistent"] = False
                result["differences"].append({
                    "field": "price",
                    "web_value": web_price,
                    "akshare_value": ak_price,
                    "diff": price_diff
                })
                # 以浏览器数据为准（更实时）
                result["recommended_data"]["price"] = web_price
            else:
                result["recommended_data"]["price"] = web_price
        
        # 对比涨跌幅
        web_change = web_data.get("change_pct")
        ak_change = akshare_data.get("change_pct")
        
        if web_change and ak_change:
            change_diff = abs(web_change - ak_change)
            if change_diff > 0.01:  # 允许0.01%的误差
                result["is_consistent"] = False
                result["differences"].append({
                    "field": "change_pct",
                    "web_value": web_change,
                    "akshare_value": ak_change,
                    "diff": change_diff
                })
                result["recommended_data"]["change_pct"] = web_change
        
        return result


# 使用示例和Agent集成说明
AGENT_INTEGRATION_GUIDE = """
## 在Agent中使用浏览器MCP获取实时行情

### Claude Code / Cursor 等支持浏览器工具的Agent

```python
# 1. 生成获取行情的浏览器任务
fetcher = WebDataFetcher()
prompt = fetcher.generate_browser_prompt("159928")

# 2. 调用浏览器Agent (示例伪代码)
# result = browser_subagent(
#     TaskName="获取159928实时行情",
#     Task=prompt,
#     RecordingName="get_realtime_quote"
# )

# 3. 解析返回的数据
# web_data = fetcher.parse_eastmoney_data(result)

# 4. 与AKShare数据对比验证
# validation = fetcher.validate_against_akshare(web_data, akshare_data)
# if not validation["is_consistent"]:
#     print("数据不一致，使用浏览器数据:", validation["recommended_data"])
```

### 数据源优先级

1. **浏览器MCP**: 最实时，但需要Agent环境支持
2. **AKShare API**: 稳定可靠，但可能有延迟
3. **本地缓存**: 离线可用，但可能过期

### 使用场景

- 盘中实时交易信号
- AKShare数据异常时的验证
- 需要秒级更新的场景
"""


if __name__ == "__main__":
    fetcher = WebDataFetcher()
    
    # 生成浏览器任务提示
    print("=== 浏览器数据获取模块 ===")
    print()
    print("生成获取159928行情的浏览器任务：")
    print("-" * 50)
    prompt = fetcher.generate_browser_prompt("159928")
    print(prompt)
    print()
    print("=== Agent集成指南 ===")
    print(AGENT_INTEGRATION_GUIDE)
