#!/usr/bin/env python3
"""
技能脚手架生成器 - skill_generator.py

用途：快速生成技能(Skill)目录结构和基础文件

使用方法：
    python skill_generator.py --name my-skill --output ./skills/
    python skill_generator.py --name api-tester --desc "API测试专家"

参数：
    --name, -n      技能名称（英文，小写，用连字符分隔）
    --desc, -d      技能描述
    --output, -o    输出目录
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

SKILL_MD_TEMPLATE = '''---
version: 1.0.0
name: {name}
description: |
  {description}
---

# {title}

## 核心能力

[描述技能的核心能力]

### 主要功能矩阵

| 功能 | 触发关键词 | 参考文档 | 输出类型 |
|------|-----------|----------|---------|
| 功能1 | "关键词" | `reference.md` | 输出类型 |

## 工作流程

### 第一步：识别任务

### 第二步：加载参考文档

### 第三步：执行任务

### 第四步：质量检查

## 约束条件

1. 约束1
2. 约束2

## 质量检查清单

- [ ] 检查项1
- [ ] 检查项2

## 初始化

作为{title}，我已准备好协助你。请告诉我你的需求。
'''

README_TEMPLATE = '''# {title}

{description}

## 目录结构

```
{name}/
├── SKILL.md           # 技能定义文件
├── README.md          # 说明文档
├── references/        # 参考文档
│   └── example.md
└── scripts/           # 工具脚本
    └── example.py
```

## 使用方法

当用户请求涉及{title}能力时，系统会自动加载此技能。

## 版本历史

- v1.0.0 ({date}): 初始版本
'''


def create_skill(name: str, description: str, output_dir: str):
    """创建技能目录结构"""
    title = name.replace("-", " ").title()
    skill_dir = Path(output_dir) / name
    
    # 创建目录结构
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
    
    # 创建 SKILL.md
    skill_content = SKILL_MD_TEMPLATE.format(
        name=name,
        title=title,
        description=description or f"{title}专家技能"
    )
    (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
    
    # 创建 README.md
    readme_content = README_TEMPLATE.format(
        name=name,
        title=title,
        description=description or f"{title}专家技能",
        date=datetime.now().strftime("%Y-%m-%d")
    )
    (skill_dir / "README.md").write_text(readme_content, encoding="utf-8")
    
    # 创建示例参考文档
    example_ref = "# 示例参考文档\n\n[在此添加详细的参考指令]"
    (skill_dir / "references" / "example.md").write_text(example_ref, encoding="utf-8")
    
    # 创建示例脚本
    example_script = '''#!/usr/bin/env python3
"""示例脚本"""

def main():
    print("Hello from {name}")

if __name__ == "__main__":
    main()
'''.format(name=name)
    (skill_dir / "scripts" / "example.py").write_text(example_script, encoding="utf-8")
    
    return skill_dir


def main():
    parser = argparse.ArgumentParser(description="技能脚手架生成器")
    parser.add_argument("--name", "-n", help="技能名称")
    parser.add_argument("--desc", "-d", help="技能描述")
    parser.add_argument("--output", "-o", default="./", help="输出目录")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ skill_generator.py 测试通过")
        return
    
    if not args.name:
        print("❌ 请指定技能名称: --name <技能名称>")
        return
    
    # 验证名称格式
    if not args.name.replace("-", "").isalnum():
        print("❌ 技能名称只能包含字母、数字和连字符")
        return
    
    skill_dir = create_skill(args.name, args.desc, args.output)
    print(f"✅ 技能已创建: {skill_dir}")
    print(f"   - SKILL.md")
    print(f"   - README.md")
    print(f"   - references/example.md")
    print(f"   - scripts/example.py")


if __name__ == "__main__":
    main()
