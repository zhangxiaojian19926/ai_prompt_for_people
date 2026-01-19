#!/usr/bin/env python3
"""
视频脚本格式化工具 - script_formatter.py

用途：格式化视频脚本，生成分镜表

使用方法：
    python script_formatter.py --input draft.md --format video --output script.md
    python script_formatter.py --input draft.md --format short --duration 60
    python script_formatter.py --list-formats

参数：
    --input, -i     输入文件
    --format, -f    格式类型: short, medium, long
    --duration, -d  目标时长（秒）
    --output, -o    输出文件
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

# 格式模板
FORMATS = {
    "short": {
        "name": "短视频脚本（15-60秒）",
        "duration": 60,
        "template": """# {title}

## 视频信息
- 时长：{duration}秒
- 平台：抖音/快手/Shorts
- 类型：短视频

## 分镜脚本

| 时间 | 画面 | 台词/旁白 | 字幕 |
|------|------|----------|------|
{storyboard}

## 字幕全文
{script_text}

## 拍摄提示
- Hook：开场3秒内抓住注意力
- 节奏：快节奏剪辑
- 字幕：重点内容需要字幕强调
"""
    },
    "medium": {
        "name": "中视频脚本（3-10分钟）",
        "duration": 300,
        "template": """# {title}

## 视频信息
- 时长：{duration}秒 ({minutes}分钟)
- 平台：B站/YouTube
- 类型：知识内容

## 内容大纲
{outline}

## 分镜脚本

| 时间 | 画面 | 台词/旁白 | 资料/字幕 |
|------|------|----------|----------|
{storyboard}

## 完整文字稿
{script_text}

## 后期提示
- 配乐：[背景音乐建议]
- 转场：[转场效果建议]
- 字幕：[字幕样式建议]
"""
    },
    "long": {
        "name": "长视频脚本（10分钟+）",
        "duration": 900,
        "template": """# {title}

## 视频信息
- 时长：{duration}秒 ({minutes}分钟)
- 平台：YouTube/B站
- 类型：深度内容

## 章节划分
{chapters}

## 内容大纲
{outline}

## 分章节脚本

{chapter_scripts}

## 完整文字稿
{script_text}

## 制作提示
- 开场：[开场设计]
- 片头：[片头动画]
- 章节标记：[章节跳转设计]
- 片尾：[结束CTA]
"""
    }
}


def extract_paragraphs(text: str) -> list:
    """提取段落"""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def estimate_duration(text: str, speed: int = 3) -> int:
    """估算朗读时长（秒），假设每秒3个字"""
    words = len(text.replace('\n', '').replace(' ', ''))
    return max(5, words // speed)


def generate_storyboard(paragraphs: list, total_duration: int) -> str:
    """生成分镜表"""
    if not paragraphs:
        return "| 0:00-0:05 | [开场] | [待填写] | [待填写] |"
    
    lines = []
    current_time = 0
    para_duration = max(5, total_duration // len(paragraphs))
    
    for i, para in enumerate(paragraphs[:10]):  # 限制10个段落
        end_time = current_time + para_duration
        time_str = f"{current_time//60}:{current_time%60:02d}-{end_time//60}:{end_time%60:02d}"
        
        # 截取前30字作为台词预览
        script_preview = para[:30] + "..." if len(para) > 30 else para
        
        lines.append(f"| {time_str} | [场景{i+1}] | {script_preview} | [字幕] |")
        current_time = end_time
    
    return "\n".join(lines)


def generate_outline(paragraphs: list) -> str:
    """生成大纲"""
    outline = []
    for i, para in enumerate(paragraphs[:5], 1):
        title = para.split('\n')[0][:20] + "..." if len(para) > 20 else para.split('\n')[0]
        outline.append(f"{i}. {title}")
    return "\n".join(outline)


def format_script(text: str, format_type: str, title: str, duration: int = None) -> str:
    """格式化脚本"""
    if format_type not in FORMATS:
        format_type = "medium"
    
    fmt = FORMATS[format_type]
    target_duration = duration or fmt["duration"]
    
    paragraphs = extract_paragraphs(text)
    
    result = fmt["template"].format(
        title=title or "视频标题",
        duration=target_duration,
        minutes=target_duration // 60,
        storyboard=generate_storyboard(paragraphs, target_duration),
        script_text=text,
        outline=generate_outline(paragraphs),
        chapters="1. 开场\n2. 主体内容\n3. 总结",
        chapter_scripts="[按章节展开脚本]"
    )
    
    return result


def list_formats():
    """列出可用格式"""
    print("🎬 可用视频脚本格式:\n")
    for key, fmt in FORMATS.items():
        print(f"  - {key}: {fmt['name']} (默认{fmt['duration']}秒)")
    print()


def main():
    parser = argparse.ArgumentParser(description="视频脚本格式化工具")
    parser.add_argument("--input", "-i", help="输入文件")
    parser.add_argument("--format", "-f", default="medium",
                        choices=list(FORMATS.keys()),
                        help="格式类型")
    parser.add_argument("--duration", "-d", type=int, help="目标时长（秒）")
    parser.add_argument("--title", "-t", help="视频标题")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--list-formats", action="store_true", help="列出可用格式")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ script_formatter.py 测试通过")
        return
    
    if args.list_formats:
        list_formats()
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 格式化
    result = format_script(text, args.format, args.title, args.duration)
    
    # 输出
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"✅ 脚本已保存到: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
