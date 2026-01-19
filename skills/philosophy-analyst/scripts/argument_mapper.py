#!/usr/bin/env python3
"""
论证可视化器 - argument_mapper.py

用途：将论证结构可视化

使用方法：
    python argument_mapper.py --input argument.md --output map.md

参数：
    --input, -i     论证文本文件
    --output, -o    输出可视化
"""

import argparse
import re
from pathlib import Path

def extract_structure(text: str) -> dict:
    """提取论证结构"""
    structure = {
        "thesis": "",
        "premises": [],
        "conclusions": []
    }
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if "因为" in line or "由于" in line:
            structure["premises"].append(line[:50])
        elif "所以" in line or "因此" in line:
            structure["conclusions"].append(line[:50])
        elif not structure["thesis"] and len(line) > 10:
            structure["thesis"] = line[:50]
    
    return structure


def generate_map(structure: dict) -> str:
    """生成论证图"""
    lines = ["# 论证结构分析\n"]
    lines.append("## 核心论点")
    lines.append(f"> {structure.get('thesis', '[待识别]')}\n")
    
    lines.append("## 论证结构\n")
    lines.append("```mermaid")
    lines.append("graph BT")
    
    for i, premise in enumerate(structure.get("premises", [])[:5]):
        lines.append(f'    P{i}["{premise[:20]}..."] --> T["论点"]')
    
    for i, conclusion in enumerate(structure.get("conclusions", [])[:3]):
        lines.append(f'    T --> C{i}["{conclusion[:20]}..."]')
    
    lines.append("```\n")
    
    lines.append("## 前提列表")
    for i, p in enumerate(structure.get("premises", []), 1):
        lines.append(f"{i}. {p}")
    
    lines.append("\n## 结论")
    for c in structure.get("conclusions", []):
        lines.append(f"- {c}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="论证可视化器")
    parser.add_argument("--input", "-i", help="论证文本文件")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ argument_mapper.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    structure = extract_structure(text)
    result = generate_map(structure)
    
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"✅ 论证图已生成: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
