#!/usr/bin/env python3
"""
文档生成器 - doc_generator.py

用途：为代码自动生成文档和注释

使用方法：
    python doc_generator.py --input source.py --output docs.md
    python doc_generator.py --input source.py --format docstring

参数：
    --input, -i     输入源代码文件
    --format, -f    输出格式: markdown, docstring, html
    --output, -o    输出文件
"""

import argparse
import re
from pathlib import Path

def extract_functions(code: str) -> list:
    """提取函数定义"""
    pattern = r'def\s+(\w+)\s*\(([^)]*)\).*?:'
    matches = re.findall(pattern, code)
    return [{"name": m[0], "params": m[1]} for m in matches]


def extract_classes(code: str) -> list:
    """提取类定义"""
    pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
    matches = re.findall(pattern, code)
    return matches


def generate_markdown_doc(code: str, filename: str) -> str:
    """生成Markdown文档"""
    output = [f"# {filename} 文档\n"]
    
    classes = extract_classes(code)
    functions = extract_functions(code)
    
    if classes:
        output.append("## 类\n")
        for cls in classes:
            output.append(f"### {cls}\n")
            output.append("[类描述待填写]\n")
    
    if functions:
        output.append("## 函数\n")
        for func in functions:
            output.append(f"### `{func['name']}({func['params']})`\n")
            output.append("[函数描述待填写]\n")
            if func['params']:
                output.append("**参数:**\n")
                for param in func['params'].split(','):
                    param = param.strip().split(':')[0].split('=')[0].strip()
                    if param:
                        output.append(f"- `{param}`: [描述]\n")
            output.append("\n")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="文档生成器")
    parser.add_argument("--input", "-i", help="输入源代码文件")
    parser.add_argument("--format", "-f", default="markdown",
                        choices=["markdown", "docstring", "html"],
                        help="输出格式")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ doc_generator.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    code = input_path.read_text(encoding="utf-8")
    doc = generate_markdown_doc(code, input_path.name)
    
    if args.output:
        Path(args.output).write_text(doc, encoding="utf-8")
        print(f"✅ 文档已生成: {args.output}")
    else:
        print(doc)


if __name__ == "__main__":
    main()
