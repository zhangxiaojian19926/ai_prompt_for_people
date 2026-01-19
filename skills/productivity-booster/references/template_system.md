# 模板系统参考文档

## 概述

模板系统用于快速生成标准文档，支持变量替换和内置模板库。

## 内置模板

| 模板名 | 用途 | 变量 |
|--------|------|------|
| `meeting` | 会议纪要 | title, date, attendees, agenda |
| `weekly_report` | 周报 | week, completed, in_progress |
| `sop` | 标准操作流程 | title, version, purpose, steps |
| `prd` | 产品需求文档 | product_name, features, goals |

## 变量语法

### 基本变量
```
{{variable_name}}
```

### 默认变量（自动填充）
| 变量 | 说明 | 示例 |
|------|------|------|
| `{{date}}` | 当前日期 | 2024-01-15 |
| `{{time}}` | 当前时间 | 14:30 |
| `{{year}}` | 当前年份 | 2024 |
| `{{month}}` | 当前月份 | 01 |
| `{{week}}` | 当前周 | 第3周 |

## 变量配置文件

```json
{
  "title": "项目周会",
  "attendees": ["张三", "李四", "王五"],
  "agenda": [
    "项目进度汇报",
    "问题讨论",
    "下周计划"
  ],
  "location": "会议室A"
}
```

## 模板示例

### 会议纪要模板
```markdown
# {{title}}

## 会议信息
- 日期：{{date}}
- 时间：{{time}}
- 地点：{{location}}
- 参会人：{{attendees}}

## 议程
{{agenda}}

## 讨论要点
[待填写]

## 行动项
| 任务 | 负责人 | 截止日期 |
|------|--------|---------|
|      |        |         |
```

## Python 脚本使用

```bash
# 查看可用模板
python scripts/apply_template.py --list-templates

# 使用内置模板
python scripts/apply_template.py -t meeting -v '{"title":"周会"}' -o meeting.md

# 使用变量文件
python scripts/apply_template.py -t weekly_report -v config.json -o report.md

# 使用自定义模板文件
python scripts/apply_template.py -t ./my_template.md -v vars.json -o output.md
```

## 创建自定义模板

1. 创建模板文件 `templates/my_template.md`
2. 使用 `{{variable}}` 标记变量位置
3. 创建变量配置文件
4. 运行脚本生成文档

```markdown
# {{project_name}} 项目报告

## 项目概述
{{description}}

## 进度
{{progress}}

## 风险
{{risks}}

---
*报告人：{{author}}*
*日期：{{date}}*
```

## 质量标准

- ✅ 变量完整替换
- ✅ 格式保持正确
- ✅ 未替换变量标记为 [待填写]
- ✅ 默认变量自动填充
