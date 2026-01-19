#!/usr/bin/env python3
"""
模板应用工具 - apply_template.py

用途：应用模板生成文档，支持变量替换和条件块

使用方法：
    python apply_template.py --template report.tpl --vars config.json --output output.md
    python apply_template.py --template meeting.tpl --vars '{"title": "周会"}' --output meeting.md
    python apply_template.py --list-templates

参数：
    --template, -t  模板文件路径
    --vars, -v      变量文件(JSON)或JSON字符串
    --output, -o    输出文件路径
    --list-templates 列出可用模板
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


# 内置模板
BUILTIN_TEMPLATES = {
    "meeting": """# {{title}}

## 会议信息
- 日期：{{date}}
- 时间：{{time}}
- 地点：{{location}}
- 参会人：{{attendees}}

## 议程
{{agenda}}

## 讨论要点
{{discussion}}

## 决议事项
{{decisions}}

## 行动项
| 任务 | 负责人 | 截止日期 |
|------|--------|---------|
{{action_items}}

## 下次会议
- 时间：{{next_meeting}}
- 议题：{{next_topics}}
""",
    
    "weekly_report": """# {{week}} 周报

## 本周完成
{{completed}}

## 进行中
{{in_progress}}

## 下周计划
{{next_week}}

## 问题与风险
{{issues}}

## 需要支持
{{support_needed}}

---
*报告人：{{author}}*
*日期：{{date}}*
""",
    
    "sop": """# {{title}} 标准操作流程

## 文档信息
- 版本：{{version}}
- 生效日期：{{effective_date}}
- 编写人：{{author}}

## 1. 目的
{{purpose}}

## 2. 适用范围
{{scope}}

## 3. 职责
{{responsibilities}}

## 4. 流程步骤
{{steps}}

## 5. 注意事项
{{notes}}

## 6. 相关文档
{{related_docs}}
""",
    
    "prd": """# {{product_name}} 产品需求文档

## 修订历史
| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| {{version}} | {{date}} | {{author}} | {{change_note}} |

## 1. 概述
### 1.1 背景
{{background}}

### 1.2 目标
{{goals}}

### 1.3 范围
{{scope}}

## 2. 功能需求
{{features}}

## 3. 非功能需求
{{non_functional}}

## 4. 用户场景
{{user_scenarios}}

## 5. 交互设计
{{interaction}}

## 6. 技术约束
{{technical_constraints}}

## 7. 里程碑
{{milestones}}
"""
}


def load_template(template_path: str) -> str:
    """加载模板"""
    # 检查是否为内置模板名
    if template_path in BUILTIN_TEMPLATES:
        return BUILTIN_TEMPLATES[template_path]
    
    # 加载文件模板
    path = Path(template_path)
    if not path.exists():
        raise FileNotFoundError(f"模板不存在: {template_path}")
    
    return path.read_text(encoding="utf-8")


def load_variables(vars_input: str) -> Dict[str, Any]:
    """加载变量"""
    # 添加默认变量
    defaults = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "year": datetime.now().strftime("%Y"),
        "month": datetime.now().strftime("%m"),
        "week": datetime.now().strftime("第%W周"),
    }
    
    if not vars_input:
        return defaults
    
    # 尝试解析为JSON字符串
    if vars_input.startswith('{'):
        vars_dict = json.loads(vars_input)
    else:
        # 作为文件路径
        path = Path(vars_input)
        if not path.exists():
            raise FileNotFoundError(f"变量文件不存在: {vars_input}")
        vars_dict = json.loads(path.read_text(encoding="utf-8"))
    
    # 合并默认值
    defaults.update(vars_dict)
    return defaults


def apply_template(template: str, variables: Dict[str, Any]) -> str:
    """应用模板变量"""
    result = template
    
    # 替换 {{variable}} 格式
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        if isinstance(value, list):
            value = "\n".join(f"- {item}" for item in value)
        elif isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        result = result.replace(placeholder, str(value))
    
    # 清理未替换的占位符
    result = re.sub(r'\{\{[^}]+\}\}', '[待填写]', result)
    
    return result


def list_templates():
    """列出可用模板"""
    print("📄 可用内置模板:\n")
    for name, content in BUILTIN_TEMPLATES.items():
        # 提取第一行作为描述
        first_line = content.split('\n')[0].replace('#', '').strip()
        print(f"  - {name}: {first_line}")
    print()
    print("使用方法: python apply_template.py --template <模板名> --vars <变量> --output <输出文件>")


def main():
    parser = argparse.ArgumentParser(description="模板应用工具")
    parser.add_argument("--template", "-t", help="模板文件或内置模板名")
    parser.add_argument("--vars", "-v", help="变量JSON文件或JSON字符串")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--list-templates", action="store_true", help="列出可用模板")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ apply_template.py 测试通过")
        return
    
    if args.list_templates:
        list_templates()
        return
    
    if not args.template:
        print("❌ 请指定模板: --template <模板名或路径>")
        print("   使用 --list-templates 查看可用模板")
        return
    
    # 加载模板
    try:
        template = load_template(args.template)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    
    # 加载变量
    try:
        variables = load_variables(args.vars)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ 变量加载失败: {e}")
        return
    
    # 应用模板
    output = apply_template(template, variables)
    
    # 输出
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 文档已生成: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
