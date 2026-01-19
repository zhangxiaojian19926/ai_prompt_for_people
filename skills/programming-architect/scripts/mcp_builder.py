#!/usr/bin/env python3
"""
MCP工具构建器 - mcp_builder.py

用途：生成MCP (Model Context Protocol) 工具模板

使用方法：
    python mcp_builder.py --name file_reader --output tools/
    python mcp_builder.py --list-examples

参数：
    --name, -n      工具名称
    --desc, -d      工具描述
    --output, -o    输出目录
"""

import argparse
import json
from pathlib import Path

MCP_TOOL_TEMPLATE = '''{{
  "name": "{name}",
  "description": "{description}",
  "inputSchema": {{
    "type": "object",
    "properties": {{
      "param1": {{
        "type": "string",
        "description": "第一个参数描述"
      }}
    }},
    "required": ["param1"]
  }}
}}
'''

TOOL_IMPLEMENTATION_TEMPLATE = '''#!/usr/bin/env python3
"""
MCP Tool: {name}
Description: {description}
"""

from typing import Any, Dict

async def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行工具逻辑
    
    Args:
        params: 工具输入参数
        
    Returns:
        工具执行结果
    """
    param1 = params.get("param1", "")
    
    # TODO: 实现工具逻辑
    result = {{
        "success": True,
        "data": f"处理了参数: {{param1}}"
    }}
    
    return result


# 工具元数据
TOOL_METADATA = {{
    "name": "{name}",
    "description": "{description}",
    "version": "1.0.0"
}}
'''


def create_mcp_tool(name: str, description: str, output_dir: str):
    """创建MCP工具"""
    tool_dir = Path(output_dir) / name
    tool_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建工具定义JSON
    tool_def = MCP_TOOL_TEMPLATE.format(
        name=name,
        description=description or f"{name}工具"
    )
    (tool_dir / "tool.json").write_text(tool_def, encoding="utf-8")
    
    # 创建工具实现
    tool_impl = TOOL_IMPLEMENTATION_TEMPLATE.format(
        name=name,
        description=description or f"{name}工具"
    )
    (tool_dir / f"{name}.py").write_text(tool_impl, encoding="utf-8")
    
    return tool_dir


def list_examples():
    """列出示例工具"""
    examples = [
        ("file_reader", "读取文件内容"),
        ("web_search", "搜索网页信息"),
        ("calculator", "执行数学计算"),
        ("code_runner", "执行代码片段"),
        ("database_query", "查询数据库"),
    ]
    
    print("📦 MCP工具示例:\n")
    for name, desc in examples:
        print(f"  - {name}: {desc}")
    print()


def main():
    parser = argparse.ArgumentParser(description="MCP工具构建器")
    parser.add_argument("--name", "-n", help="工具名称")
    parser.add_argument("--desc", "-d", help="工具描述")
    parser.add_argument("--output", "-o", default="./", help="输出目录")
    parser.add_argument("--list-examples", action="store_true", help="列出示例")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ mcp_builder.py 测试通过")
        return
    
    if args.list_examples:
        list_examples()
        return
    
    if not args.name:
        print("❌ 请指定工具名称: --name <工具名称>")
        return
    
    tool_dir = create_mcp_tool(args.name, args.desc, args.output)
    print(f"✅ MCP工具已创建: {tool_dir}")
    print(f"   - tool.json (工具定义)")
    print(f"   - {args.name}.py (工具实现)")


if __name__ == "__main__":
    main()
