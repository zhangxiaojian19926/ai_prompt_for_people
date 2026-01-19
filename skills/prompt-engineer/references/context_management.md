# 长上下文管理参考

## 概述

当文本超出模型上下文窗口时，需要采用分块、压缩或优先级策略处理。

## 上下文限制

| 模型 | 上下文窗口 |
|------|-----------|
| GPT-4 | 8K / 128K |
| Claude | 100K-200K |
| Gemini | 1M+ |

## 分块策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **固定大小** | 按token数切分 | 通用场景 |
| **语义分割** | 按标题/段落切分 | 结构化文档 |
| **滑动窗口** | 带重叠的分块 | 需要上下文连贯 |

## 优先级规则

```markdown
## 内容优先级
1. 🔴 必须保留：核心指令、关键约束
2. 🟡 重要保留：示例、上下文背景
3. 🟢 可压缩：详细说明、冗余内容
```

## 压缩方法

1. **摘要替换**：长段落替换为摘要
2. **重复删除**：删除重复内容
3. **格式精简**：移除非必要格式

## 分块输出格式

```
chunk_001.md - 2000 tokens
chunk_002.md - 1800 tokens
chunk_003.md - 2100 tokens
```

## Python脚本

```bash
# 分析文本
python scripts/context_splitter.py --input doc.md --analyze

# 分块处理
python scripts/context_splitter.py --input doc.md --max-tokens 4000 --output chunks/

# 语义分割
python scripts/context_splitter.py --input doc.md --strategy semantic
```

## 质量检查
- [ ] 分块策略是否合理？
- [ ] 关键信息是否保留？
- [ ] 上下文是否连贯？
- [ ] 是否有信息丢失？
