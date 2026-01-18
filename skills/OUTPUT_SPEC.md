# 技能输出目录规范

## 统一输出目录结构

所有技能生成的内容统一保存到 `outputs/` 目录：

```
outputs/
├── articles/                    # content-creator 输出
│   └── YYYY-MM-DD_标题/
│       ├── README.md
│       ├── article.md
│       ├── images/
│       └── sources/
│
├── code/                        # programming-architect 输出
│   └── YYYY-MM-DD_项目名/
│       ├── README.md
│       ├── architecture.md
│       ├── pseudocode/
│       ├── diagrams/
│       └── docs/
│
├── prompts/                     # prompt-engineer 输出
│   └── YYYY-MM-DD_提示词名/
│       ├── README.md
│       ├── prompt.md
│       └── versions/
│
├── knowledge/                   # knowledge-engineer 输出
│   └── YYYY-MM-DD_主题/
│       ├── README.md
│       ├── analysis.md
│       ├── knowledge_graph.md
│       └── notes/
│
├── documents/                   # productivity-booster 输出
│   └── YYYY-MM-DD_文档名/
│       ├── README.md
│       ├── output.md
│       └── assets/
│
├── business/                    # business-strategist 输出
│   └── YYYY-MM-DD_项目名/
│       ├── README.md
│       ├── report.md
│       ├── data/
│       └── charts/
│
└── philosophy/                  # philosophy-analyst 输出
    └── YYYY-MM-DD_主题/
        ├── README.md
        ├── analysis.md
        └── diagrams/
```

## 目录命名规范

1. **日期前缀**：`YYYY-MM-DD_` 格式，便于排序
2. **标题简洁**：使用简短有意义的名称，用下划线连接
3. **避免特殊字符**：不使用空格、中文标点等

## 每个输出目录必备文件

### README.md 模板

```markdown
# [项目/文章标题]

## 基本信息
- **创建时间**：YYYY-MM-DD HH:mm
- **技能来源**：[技能名称]
- **任务类型**：[类型描述]

## 文件清单
| 文件 | 说明 |
|------|------|
| xxx.md | 主要输出 |
| ... | ... |

## 使用说明
[如何使用这些输出]
```

## 快速创建命令

```bash
# 创建文章目录
mkdir -p outputs/articles/$(date +%Y-%m-%d)_标题/{images,sources}

# 创建代码目录
mkdir -p outputs/code/$(date +%Y-%m-%d)_项目名/{pseudocode,diagrams,docs}

# 创建知识目录
mkdir -p outputs/knowledge/$(date +%Y-%m-%d)_主题/notes
```
