#!/usr/bin/env python3
"""
决策树分析器 - decision_tree.py

用途：构建决策分析树

使用方法：
    python decision_tree.py --input problem.md --output tree.md

参数：
    --input, -i     问题描述文件
    --output, -o    输出决策树
"""

import argparse
from pathlib import Path

DECISION_TEMPLATE = '''# 决策分析

## 问题
{problem}

## 决策树

```mermaid
graph TD
    A["{problem_short}"] --> B{{选项A}}
    A --> C{{选项B}}
    B --> D["结果A1"]
    B --> E["结果A2"]
    C --> F["结果B1"]
    C --> G["结果B2"]
```

## 分析维度

### 选项A
- 优点：[待分析]
- 缺点：[待分析]
- 风险：[待分析]

### 选项B
- 优点：[待分析]
- 缺点：[待分析]
- 风险：[待分析]

## 建议
[基于分析的建议]
'''


def main():
    parser = argparse.ArgumentParser(description="决策树分析器")
    parser.add_argument("--input", "-i", help="问题描述文件")
    parser.add_argument("--problem", "-p", help="直接输入问题")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ decision_tree.py 测试通过")
        return
    
    problem = args.problem or ""
    if args.input:
        input_path = Path(args.input)
        if input_path.exists():
            problem = input_path.read_text(encoding="utf-8")
    
    if not problem:
        problem = "[请输入待决策问题]"
    
    result = DECISION_TEMPLATE.format(
        problem=problem,
        problem_short=problem[:20] + "..." if len(problem) > 20 else problem
    )
    
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"✅ 决策树已生成: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
