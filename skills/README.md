# 技能使用指南

本目录包含**7个**基于 skill-creator 创建的专业技能，每个技能都整合了对应领域的精选提示词。

## 技能列表

| 技能名称 | 功能描述 |
|---------|---------|
| **prompt-engineer** | 🆕 提示词工程与优化（元能力） |
| **programming-architect** | 全栈编程架构分析与代码生成 |
| **knowledge-engineer** | 深度学习与知识工程 |
| **productivity-booster** | 生产力增强与文档处理 |
| **content-creator** | 内容创作与文案撰写 |
| **business-strategist** | 商业战略分析与市场洞察 |
| **philosophy-analyst** | 哲学思维与逻辑分析 |

## 使用方式

### 方式一：直接调用（推荐）

在对话中直接提及相关任务关键词，技能会自动触发：

```
你：帮我分析一下这个项目的架构

你：用伪代码描述一下用户登录流程

你：帮我写一篇关于AI的推特串文

你：分析一下电动汽车行业的竞争格局

你：对"自由意志"这个概念进行深度分析

你：把这个PDF转成Markdown格式
```

### 方式二：打包安装

1. **打包单个技能**：
```bash
python3 /Users/zhangjiang/.claude/plugins/cache/anthropic-agent-skills/example-skills/69c0b1a06741/skills/skill-creator/scripts/package_skill.py skills/programming-architect
```

2. **打包所有技能**：
```bash
for skill in skills/*/; do
  python3 /Users/zhangjiang/.claude/plugins/cache/anthropic-agent-skills/example-skills/69c0b1a06741/skills/skill-creator/scripts/package_skill.py "$skill"
done
```

3. **安装到Claude Code**：
   - 将生成的 `.skill` 文件复制到 `~/.claude/skills/` 目录
   - 重启 Claude Code

## 技能触发关键词

### programming-architect（编程架构师）
- "分析架构"、"代码结构"、"项目分析"
- "伪代码"、"逻辑流程"、"步骤分解"
- "序列图"、"时序图"、"交互流程"
- "项目文档"、"上下文文档"
- "函数化"、"模块分解"
- "代码审计"、"安全检查"

### knowledge-engineer（知识工程师）
- "深度分析"、"思维模型"
- "概念解析"、"什么是"、"如何理解"
- "书籍分析"、"论文解析"
- "学习方法"、"学习框架"
- "隐性知识"、"专家经验"
- "知识图谱"、"知识体系"

### productivity-booster（生产力专家）
- "PDF转MD"、"扫描文档"
- "排版"、"格式化"
- "校对"、"OCR"
- "SOP"、"工作流"
- "润色"、"人性化"
- "文档结构化"

### content-creator（内容创作者）
- "推特串文"、"Twitter"
- "小红书"、"朋友圈文案"
- "模仿风格"、"仿写"
- "文章"、"通讯"、"博客"
- "营销文案"
- "内容结构"

### business-strategist（商业战略师）
- "行业分析"、"市场分析"
- "战略决策"、"SWOT"
- "商业报告"、"白皮书"
- "创意验证"、"想法评估"
- "竞争分析"
- "商业模式"

### philosophy-analyst（哲学分析师）
- "命题分析"、"深度提取"
- "辩证分析"、"矛盾分析"
- "批判性思维"
- "结构分析"、"溯源分析"
- "哲学分析"、"概念解构"
- "逻辑漏洞"

## 技能结构说明

每个技能目录包含：

```
skill-name/
├── SKILL.md              # 主技能文件（必需）
└── references/           # 参考文档（可选）
    ├── *.md              # 详细提示词参考
    └── ...
```

### SKILL.md 结构

- **YAML Frontmatter**：技能名称和描述（用于触发判断）
- **功能矩阵**：主要功能和触发关键词
- **工作流程**：任务识别→执行→输出
- **约束条件**：使用限制和质量要求

### references/ 目录

存放详细的提示词模板，技能执行时按需加载。

## 扩展技能

### 添加新的参考文档

1. 进入对应技能目录：
```bash
cd skills/programming-architect/references/
```

2. 创建新的参考文档：
```bash
# 从提示词文件中提取相关内容
nano new_reference.md
```

3. 在 SKILL.md 中添加引用：
```markdown
| 新功能 | "触发词" | `new_reference.md` |
```

### 修改技能

直接编辑 `SKILL.md` 文件，修改后无需重新打包，立即生效。

## 常见问题

**Q: 技能没有自动触发？**

A: 确保使用明确的关键词，参考上表的触发词列表。

**Q: 如何查看技能使用的是什么提示词？**

A: 检查 `references/` 目录下的对应参考文档。

**Q: 可以同时使用多个技能吗？**

A: 可以，Claude 会根据任务类型自动选择最合适的技能。

**Q: 如何禁用某个技能？**

A: 删除或重命名对应技能的 `.skill` 文件。

## 技能来源

这些技能基于 `prompts_extracted/` 目录中的提示词创建：

- **编程** (62个提示词) → programming-architect
- **学习教育** (47个提示词) → knowledge-engineer
- **生产力** (40个提示词) → productivity-booster
- **内容创作** (22个提示词) → content-creator
- **商业分析** (8个提示词) → business-strategist
- **哲学工具箱** (21个提示词) → philosophy-analyst

## 贡献与反馈

如需添加新技能或改进现有技能，请参考 skill-creator 的文档。

---

创建时间：2026-01-10
基于提示词版本：v1.0
