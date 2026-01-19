# Agent提示词设计参考

## 概述

Agent提示词用于设计能够使用工具、进行多步推理的智能代理。

## 推理模式

| 模式 | 特点 | 适用场景 |
|------|------|---------|
| **ReAct** | 思考-行动-观察循环 | 工具调用、多步任务 |
| **CoT** | 链式逐步推理 | 复杂逻辑、数学 |
| **ToT** | 树状多路径探索 | 创意问题、决策 |
| **Self-Ask** | 自问自答分解 | 多跳问答 |
| **RAG** | 检索增强生成 | 知识库问答 |

## ReAct格式

```
Thought: [分析当前情况]
Action: [选择工具]
Action Input: [工具参数]
Observation: [工具返回结果]
... (重复)
Final Answer: [最终答案]
```

## 工具定义

```markdown
## 可用工具
| 工具名 | 功能 | 参数 |
|--------|------|------|
| search | 搜索信息 | query: 关键词 |
| calculate | 数学计算 | expression: 表达式 |
```

## 安全边界

必须包含：
- 禁止的操作列表
- 敏感信息处理规则
- 失败时的回退策略

```markdown
## 安全边界
- 禁止：执行删除操作
- 禁止：访问未授权数据
- 失败时：返回错误说明
```

## Python脚本

```bash
python scripts/agent_builder.py --mode react --tools "search,calculate"
python scripts/agent_builder.py --list-modes
```

## 质量检查
- [ ] 推理模式是否正确？
- [ ] 工具定义是否完整？
- [ ] 是否有安全边界？
- [ ] 是否有示例流程？
