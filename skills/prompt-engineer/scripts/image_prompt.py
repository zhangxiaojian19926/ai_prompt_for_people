#!/usr/bin/env python3
"""
图像提示词生成器 - image_prompt.py

用途：生成多模态（图像分析）提示词模板

使用方法：
    python image_prompt.py --task "分析产品图" --output prompt.md
    python image_prompt.py --task "OCR识别" --modality image --output prompt.md
    python image_prompt.py --list-templates

参数：
    --task          任务描述
    --modality      输入模态: image, video, audio
    --output, -o    输出文件路径
    --template      使用预设模板
    --list-templates 列出可用模板
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

# 预设模板
TEMPLATES = {
    "image_analysis": {
        "name": "图像分析",
        "modality": "image",
        "template": """# 图像分析提示词

## 模态配置
- 输入模态：图像
- 输出模态：结构化JSON

## 视觉指令

### 关注区域
分析整个图像，重点关注：
- 主体对象
- 背景环境
- 文字信息
- 颜色和布局

### 分析维度
1. **内容识别**：识别图像中的主要对象
2. **场景理解**：理解图像的整体场景
3. **细节提取**：提取关键细节信息

## 任务指令
{task_description}

## 输出格式
```json
{{
  "main_objects": [],
  "scene_description": "",
  "details": [],
  "confidence": 0.0
}}
```

## 注意事项
- 描述要客观准确
- 不要推测不确定的信息
- 对于模糊内容标注置信度
"""
    },
    "ocr": {
        "name": "OCR文字识别",
        "modality": "image",
        "template": """# OCR文字识别提示词

## 模态配置
- 输入模态：图像
- 输出模态：文本/Markdown

## 视觉指令

### 关注区域
识别图像中的所有文字内容，包括：
- 标题和正文
- 表格数据
- 标注信息
- 水印和页脚

### 识别规则
1. 保持原文格式结构
2. 表格转换为Markdown表格
3. 标注识别不确定的文字

## 任务指令
{task_description}

## 输出格式
```markdown
# [文档标题]

[识别的正文内容]

| 列1 | 列2 |
|-----|-----|
| 数据1 | 数据2 |

*[不确定内容]*
```
"""
    },
    "chart_analysis": {
        "name": "图表分析",
        "modality": "image",
        "template": """# 图表分析提示词

## 模态配置
- 输入模态：图像（图表）
- 输出模态：结构化数据 + 分析

## 视觉指令

### 图表类型识别
首先识别图表类型：
- 柱状图/条形图
- 折线图
- 饼图
- 散点图
- 其他

### 数据提取
1. 提取坐标轴标签
2. 提取数据点/数值
3. 提取图例信息

## 任务指令
{task_description}

## 输出格式
```json
{{
  "chart_type": "",
  "title": "",
  "x_axis": {{"label": "", "values": []}},
  "y_axis": {{"label": "", "range": []}},
  "data_series": [],
  "insights": []
}}
```
"""
    },
    "video_analysis": {
        "name": "视频分析",
        "modality": "video",
        "template": """# 视频分析提示词

## 模态配置
- 输入模态：视频
- 输出模态：时间线标注 + 摘要

## 分析指令

### 时间线分割
将视频按场景变化分割为片段。

### 分析维度
1. **场景识别**：每个片段的场景描述
2. **动作识别**：关键动作和事件
3. **语音内容**：对话或旁白（如有）
4. **情感分析**：情绪和氛围

## 任务指令
{task_description}

## 输出格式
```json
{{
  "duration": "00:00:00",
  "segments": [
    {{
      "start": "00:00:00",
      "end": "00:00:10",
      "scene": "",
      "actions": [],
      "transcript": ""
    }}
  ],
  "summary": ""
}}
```
"""
    }
}


def list_templates():
    """列出可用模板"""
    print("📄 可用多模态提示词模板:\n")
    for key, template in TEMPLATES.items():
        print(f"  - {key}: {template['name']} ({template['modality']})")
    print()
    print("使用方法: python image_prompt.py --template <模板名> --task <任务描述>")


def generate_prompt(template_name: str, task: str) -> str:
    """生成提示词"""
    if template_name not in TEMPLATES:
        template_name = "image_analysis"
    
    template = TEMPLATES[template_name]["template"]
    return template.format(task_description=task)


def main():
    parser = argparse.ArgumentParser(description="图像提示词生成器")
    parser.add_argument("--task", "-t", help="任务描述")
    parser.add_argument("--modality", "-m", default="image",
                        choices=["image", "video", "audio"],
                        help="输入模态")
    parser.add_argument("--template", default="image_analysis",
                        help="使用的模板")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--list-templates", action="store_true",
                        help="列出可用模板")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ image_prompt.py 测试通过")
        return
    
    if args.list_templates:
        list_templates()
        return
    
    if not args.task:
        print("❌ 请指定任务描述: --task <任务描述>")
        return
    
    # 生成提示词
    prompt = generate_prompt(args.template, args.task)
    
    # 输出
    if args.output:
        Path(args.output).write_text(prompt, encoding="utf-8")
        print(f"✅ 提示词已保存到: {args.output}")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
