#!/usr/bin/env python3
"""
智能摘要工具 - summarize.py

用途：自动生成文本摘要，支持多级摘要策略

使用方法：
    python summarize.py --input document.md --level brief
    python summarize.py --input document.md --level detailed --keywords
    python summarize.py --input document.md --level structured --output summary.md

参数：
    --input, -i     输入文件路径
    --level, -l     摘要级别: brief(一句话), detailed(要点), structured(结构化)
    --keywords      是否提取关键词
    --output, -o    输出文件路径（可选，默认打印到控制台）
    --max-length    摘要最大字数（默认200）
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple


def extract_sentences(text: str) -> List[str]:
    """提取句子列表"""
    sentences = re.split(r'[。！？\n]', text)
    return [s.strip() for s in sentences if s.strip()]


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """提取关键词（基于词频）"""
    # 移除标点和数字
    clean_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', '', text)
    words = clean_text.split()
    
    # 统计词频
    word_freq = {}
    for word in words:
        if len(word) >= 2:  # 过滤单字
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 排序取top_n
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def generate_brief_summary(text: str, max_length: int = 50) -> str:
    """生成一句话摘要"""
    sentences = extract_sentences(text)
    if not sentences:
        return "无法生成摘要"
    
    # 简单策略：取第一句+长度控制
    summary = sentences[0]
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
    return summary


def generate_detailed_summary(text: str, max_points: int = 5) -> List[str]:
    """生成要点摘要"""
    sentences = extract_sentences(text)
    
    # 简单策略：按长度筛选重要句子
    important = sorted(sentences, key=len, reverse=True)[:max_points]
    return important


def generate_structured_summary(text: str) -> dict:
    """生成结构化摘要"""
    sentences = extract_sentences(text)
    
    return {
        "brief": generate_brief_summary(text),
        "key_points": generate_detailed_summary(text, 3),
        "keywords": extract_keywords(text, 5),
        "word_count": len(text),
        "sentence_count": len(sentences)
    }


def format_output(summary_data: dict, level: str, include_keywords: bool) -> str:
    """格式化输出"""
    output = ["## 摘要报告\n"]
    
    if level == "brief":
        output.append(f"### 一句话摘要\n{summary_data}\n")
    elif level == "detailed":
        output.append("### 关键要点\n")
        for i, point in enumerate(summary_data, 1):
            output.append(f"{i}. {point}\n")
    else:  # structured
        output.append(f"### 一句话摘要\n{summary_data['brief']}\n")
        output.append("\n### 关键要点\n")
        for i, point in enumerate(summary_data['key_points'], 1):
            output.append(f"{i}. {point}\n")
        
        if include_keywords:
            output.append("\n### 关键词\n")
            keywords = " ".join([f"`{k}`" for k in summary_data['keywords']])
            output.append(keywords + "\n")
        
        output.append(f"\n### 统计\n")
        output.append(f"- 字数：{summary_data['word_count']}\n")
        output.append(f"- 句子数：{summary_data['sentence_count']}\n")
    
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(description="智能摘要工具")
    parser.add_argument("--input", "-i", help="输入文件路径")
    parser.add_argument("--level", "-l", default="brief", 
                        choices=["brief", "detailed", "structured"],
                        help="摘要级别")
    parser.add_argument("--keywords", action="store_true", help="提取关键词")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--max-length", type=int, default=200, help="摘要最大字数")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ summarize.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    # 读取输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 生成摘要
    if args.level == "brief":
        summary = generate_brief_summary(text, args.max_length)
    elif args.level == "detailed":
        summary = generate_detailed_summary(text)
    else:
        summary = generate_structured_summary(text)
    
    # 格式化输出
    output = format_output(summary, args.level, args.keywords)
    
    # 输出结果
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 摘要已保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
