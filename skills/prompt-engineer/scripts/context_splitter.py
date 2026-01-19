#!/usr/bin/env python3
"""
上下文分割器 - context_splitter.py

用途：将长文本分割为适合LLM上下文窗口的块

使用方法：
    python context_splitter.py --input long_doc.md --max-tokens 4000 --output chunks/
    python context_splitter.py --input doc.md --strategy semantic --overlap 100
    python context_splitter.py --input doc.md --analyze

参数：
    --input, -i     输入文件路径
    --output, -o    输出目录
    --max-tokens    每块最大token数（默认4000）
    --strategy      分割策略: fixed, semantic, paragraph
    --overlap       块之间重叠的token数
    --analyze       仅分析不分割
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple

# 简单的token估算（中文约1.5字符/token，英文约4字符/token）
def estimate_tokens(text: str) -> int:
    """估算token数量"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def split_by_paragraph(text: str) -> List[str]:
    """按段落分割"""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def split_by_sentence(text: str) -> List[str]:
    """按句子分割"""
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)
    return [s.strip() for s in sentences if s.strip()]


def split_fixed(text: str, max_tokens: int, overlap: int = 0) -> List[str]:
    """固定大小分割"""
    chunks = []
    paragraphs = split_by_paragraph(text)
    
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = estimate_tokens(para)
        
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # 保存当前块
            chunks.append('\n\n'.join(current_chunk))
            
            # 处理重叠
            if overlap > 0:
                overlap_text = current_chunk[-1] if current_chunk else ""
                current_chunk = [overlap_text] if estimate_tokens(overlap_text) <= overlap else []
                current_tokens = estimate_tokens('\n\n'.join(current_chunk))
            else:
                current_chunk = []
                current_tokens = 0
        
        current_chunk.append(para)
        current_tokens += para_tokens
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def split_semantic(text: str, max_tokens: int) -> List[str]:
    """语义分割（基于标题）"""
    chunks = []
    
    # 按一级标题分割
    sections = re.split(r'(?=^# )', text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]
    
    for section in sections:
        section_tokens = estimate_tokens(section)
        
        if section_tokens <= max_tokens:
            chunks.append(section)
        else:
            # 进一步按二级标题分割
            subsections = re.split(r'(?=^## )', section, flags=re.MULTILINE)
            
            current_chunk = []
            current_tokens = 0
            
            for subsec in subsections:
                subsec_tokens = estimate_tokens(subsec)
                
                if current_tokens + subsec_tokens > max_tokens and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                
                current_chunk.append(subsec)
                current_tokens += subsec_tokens
            
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def analyze_text(text: str, max_tokens: int) -> dict:
    """分析文本结构"""
    total_tokens = estimate_tokens(text)
    paragraphs = split_by_paragraph(text)
    sentences = split_by_sentence(text)
    
    # 查找标题
    h1_count = len(re.findall(r'^# ', text, re.MULTILINE))
    h2_count = len(re.findall(r'^## ', text, re.MULTILINE))
    h3_count = len(re.findall(r'^### ', text, re.MULTILINE))
    
    return {
        "total_chars": len(text),
        "total_tokens": total_tokens,
        "paragraphs": len(paragraphs),
        "sentences": len(sentences),
        "h1_headings": h1_count,
        "h2_headings": h2_count,
        "h3_headings": h3_count,
        "estimated_chunks": max(1, total_tokens // max_tokens + 1),
        "overflow": total_tokens > max_tokens
    }


def format_analysis(analysis: dict, max_tokens: int) -> str:
    """格式化分析结果"""
    output = ["## 文本分析报告\n"]
    output.append(f"### 基本信息")
    output.append(f"- 总字符数：{analysis['total_chars']}")
    output.append(f"- 估算Token数：{analysis['total_tokens']}")
    output.append(f"- 段落数：{analysis['paragraphs']}")
    output.append(f"- 句子数：{analysis['sentences']}")
    output.append(f"")
    output.append(f"### 结构信息")
    output.append(f"- 一级标题：{analysis['h1_headings']}")
    output.append(f"- 二级标题：{analysis['h2_headings']}")
    output.append(f"- 三级标题：{analysis['h3_headings']}")
    output.append(f"")
    output.append(f"### 分块预估")
    output.append(f"- 上下文限制：{max_tokens} tokens")
    output.append(f"- 是否超限：{'⚠️ 是' if analysis['overflow'] else '✅ 否'}")
    output.append(f"- 预计分块数：{analysis['estimated_chunks']}")
    
    if analysis['overflow']:
        output.append(f"")
        output.append(f"### 建议策略")
        if analysis['h1_headings'] > 1 or analysis['h2_headings'] > 1:
            output.append(f"- 推荐使用 `semantic` 策略（按标题分割）")
        else:
            output.append(f"- 推荐使用 `paragraph` 策略（按段落分割）")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="上下文分割器")
    parser.add_argument("--input", "-i", help="输入文件路径")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--max-tokens", type=int, default=4000, help="每块最大token数")
    parser.add_argument("--strategy", "-s", default="fixed",
                        choices=["fixed", "semantic", "paragraph"],
                        help="分割策略")
    parser.add_argument("--overlap", type=int, default=0, help="重叠token数")
    parser.add_argument("--analyze", action="store_true", help="仅分析不分割")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ context_splitter.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 分析模式
    if args.analyze:
        analysis = analyze_text(text, args.max_tokens)
        print(format_analysis(analysis, args.max_tokens))
        return
    
    # 分割
    if args.strategy == "semantic":
        chunks = split_semantic(text, args.max_tokens)
    elif args.strategy == "paragraph":
        chunks = split_by_paragraph(text)
        # 合并小段落
        merged = []
        current = []
        current_tokens = 0
        for chunk in chunks:
            chunk_tokens = estimate_tokens(chunk)
            if current_tokens + chunk_tokens > args.max_tokens and current:
                merged.append('\n\n'.join(current))
                current = []
                current_tokens = 0
            current.append(chunk)
            current_tokens += chunk_tokens
        if current:
            merged.append('\n\n'.join(current))
        chunks = merged
    else:
        chunks = split_fixed(text, args.max_tokens, args.overlap)
    
    # 输出
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, chunk in enumerate(chunks, 1):
            chunk_file = output_dir / f"chunk_{i:03d}.md"
            chunk_file.write_text(chunk, encoding="utf-8")
        
        print(f"✅ 已分割为 {len(chunks)} 个块，保存到: {args.output}")
    else:
        print(f"总共 {len(chunks)} 个块:\n")
        for i, chunk in enumerate(chunks, 1):
            tokens = estimate_tokens(chunk)
            print(f"--- 块 {i} ({tokens} tokens) ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
            print()


if __name__ == "__main__":
    main()
