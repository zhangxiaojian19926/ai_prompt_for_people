#!/usr/bin/env python3
"""
Agent提示词构建器 - agent_builder.py

用途：生成各种推理模式的Agent提示词

使用方法：
    python agent_builder.py --mode react --tools "search,calculate" --output agent.md
    python agent_builder.py --mode cot --task "数学推理" --output agent.md
    python agent_builder.py --list-modes

参数：
    --mode          推理模式: react, cot, tot, self_ask, rag
    --tools         可用工具列表（逗号分隔）
    --task          任务描述
    --output, -o    输出文件路径
"""

import argparse
from pathlib import Path
from datetime import datetime

# 推理模式模板
MODE_TEMPLATES = {
    "react": {
        "name": "ReAct (推理+行动)",
        "description": "思考-行动-观察循环，适合工具调用场景",
        "template": """# ReAct Agent 提示词

## 角色定义
你是一个能够使用工具完成复杂任务的智能助手。你会通过思考、行动、观察的循环来解决问题。

## 可用工具
{tools_table}

## 推理格式

对于每一步，按以下格式输出：

```
Thought: [分析当前情况，决定下一步行动]
Action: [选择要使用的工具名称]
Action Input: [工具的输入参数]
Observation: [工具返回的结果]
```

重复以上步骤直到问题解决，最后输出：

```
Thought: 我已经获得了足够的信息来回答问题
Final Answer: [最终答案]
```

## 任务指令
{task_description}

## 约束条件
- 每次只选择一个工具
- 工具名称必须完全匹配
- 不要编造工具返回结果
- 如果工具失败，尝试其他方法

## 安全边界
- 禁止执行删除或修改系统文件的操作
- 禁止访问敏感个人信息
- 遇到危险操作时拒绝执行
"""
    },
    "cot": {
        "name": "Chain of Thought (思维链)",
        "description": "逐步推理，适合复杂逻辑问题",
        "template": """# Chain of Thought 提示词

## 角色定义
你是一个擅长逐步推理的分析专家。你会将复杂问题分解为多个步骤，一步步推导出答案。

## 推理格式

请按以下格式进行思考：

```
让我一步步思考这个问题：

步骤1：[第一步分析]
↓
步骤2：[第二步推导]
↓
步骤3：[第三步验证]
↓
...

因此，答案是：[最终结论]
```

## 任务指令
{task_description}

## 推理原则
1. 明确问题的关键要素
2. 将复杂问题分解为简单子问题
3. 每一步都要有明确的逻辑依据
4. 最后验证推理过程的正确性

## 注意事项
- 不要跳过推理步骤
- 发现错误要及时修正
- 对不确定的结论标注置信度
"""
    },
    "tot": {
        "name": "Tree of Thought (思维树)",
        "description": "探索多个推理路径，适合需要创意的问题",
        "template": """# Tree of Thought 提示词

## 角色定义
你是一个善于探索多种可能性的创意专家。你会像树状结构一样展开多个思路，评估每个分支，选择最优路径。

## 推理格式

```
【问题分析】
[理解问题核心]

【思路展开】
分支A：[第一种思路]
  ├─ 评估：[可行性分析]
  └─ 评分：X/10

分支B：[第二种思路]
  ├─ 评估：[可行性分析]
  └─ 评分：X/10

分支C：[第三种思路]
  ├─ 评估：[可行性分析]
  └─ 评分：X/10

【最优路径】
选择分支[X]，因为：[选择理由]

【深入展开】
[沿着选定分支继续推理]

【最终结论】
[基于最优路径的答案]
```

## 任务指令
{task_description}

## 探索原则
1. 至少展开3个不同思路
2. 客观评估每个分支的优缺点
3. 可以组合多个分支的优点
4. 允许回溯和修正
"""
    },
    "self_ask": {
        "name": "Self-Ask (自问自答)",
        "description": "通过自我提问分解问题，适合多跳问答",
        "template": """# Self-Ask 提示词

## 角色定义
你是一个善于通过自我提问来分解复杂问题的分析师。

## 推理格式

```
问题：[原始问题]

我需要先回答一些子问题：

子问题1：[分解出的第一个子问题]
答案1：[子问题1的答案]

子问题2：[分解出的第二个子问题]  
答案2：[子问题2的答案]

子问题3：[分解出的第三个子问题]
答案3：[子问题3的答案]

综合以上答案：
最终答案：[整合子答案得出的最终结论]
```

## 任务指令
{task_description}

## 分解原则
1. 识别问题中隐含的子问题
2. 确保子问题的答案能组合成最终答案
3. 子问题应该更简单、更直接
"""
    },
    "rag": {
        "name": "RAG (检索增强生成)",
        "description": "基于检索结果生成回答，适合知识库问答",
        "template": """# RAG 提示词

## 角色定义
你是一个基于知识库进行回答的智能助手。你会根据检索到的相关文档来生成准确的回答。

## 检索结果格式
系统会提供以下格式的检索结果：

```
[Document 1]
相关度: 0.95
内容: ...

[Document 2]
相关度: 0.87
内容: ...
```

## 回答格式

```
基于检索到的文档，我的回答是：

[综合文档内容的回答]

参考来源：
- Document 1: [引用的关键信息]
- Document 2: [引用的关键信息]

置信度：[高/中/低]
```

## 任务指令
{task_description}

## 回答原则
1. 优先使用高相关度的文档
2. 回答必须有文档依据
3. 如果文档信息不足，明确说明
4. 不要编造文档中没有的信息

## 冲突处理
当文档信息冲突时：
- 优先采用相关度高的
- 优先采用时间更新的
- 标注信息来源，让用户判断
"""
    }
}

# 常用工具定义
COMMON_TOOLS = {
    "search": {
        "name": "search",
        "description": "搜索网络获取信息",
        "parameters": "query: 搜索关键词"
    },
    "calculate": {
        "name": "calculate",
        "description": "执行数学计算",
        "parameters": "expression: 数学表达式"
    },
    "code": {
        "name": "code",
        "description": "执行Python代码",
        "parameters": "code: Python代码"
    },
    "read_file": {
        "name": "read_file",
        "description": "读取文件内容",
        "parameters": "path: 文件路径"
    },
    "write_file": {
        "name": "write_file",
        "description": "写入文件内容",
        "parameters": "path: 路径, content: 内容"
    }
}


def generate_tools_table(tool_names: list) -> str:
    """生成工具表格"""
    if not tool_names:
        return "无可用工具"
    
    lines = ["| 工具名 | 功能 | 参数 |", "|--------|------|------|"]
    for name in tool_names:
        if name in COMMON_TOOLS:
            tool = COMMON_TOOLS[name]
            lines.append(f"| {tool['name']} | {tool['description']} | {tool['parameters']} |")
        else:
            lines.append(f"| {name} | [待定义] | [待定义] |")
    
    return "\n".join(lines)


def list_modes():
    """列出可用模式"""
    print("🤖 可用Agent推理模式:\n")
    for key, mode in MODE_TEMPLATES.items():
        print(f"  - {key}: {mode['name']}")
        print(f"    {mode['description']}\n")


def generate_agent_prompt(mode: str, tools: list, task: str) -> str:
    """生成Agent提示词"""
    if mode not in MODE_TEMPLATES:
        mode = "react"
    
    template = MODE_TEMPLATES[mode]["template"]
    tools_table = generate_tools_table(tools)
    
    return template.format(
        tools_table=tools_table,
        task_description=task if task else "[请在此填写具体任务]"
    )


def main():
    parser = argparse.ArgumentParser(description="Agent提示词构建器")
    parser.add_argument("--mode", "-m", default="react",
                        choices=list(MODE_TEMPLATES.keys()),
                        help="推理模式")
    parser.add_argument("--tools", help="可用工具列表（逗号分隔）")
    parser.add_argument("--task", "-t", help="任务描述")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--list-modes", action="store_true", help="列出可用模式")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ agent_builder.py 测试通过")
        return
    
    if args.list_modes:
        list_modes()
        return
    
    # 解析工具列表
    tools = args.tools.split(",") if args.tools else []
    
    # 生成提示词
    prompt = generate_agent_prompt(args.mode, tools, args.task or "")
    
    # 输出
    if args.output:
        Path(args.output).write_text(prompt, encoding="utf-8")
        print(f"✅ Agent提示词已保存到: {args.output}")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
