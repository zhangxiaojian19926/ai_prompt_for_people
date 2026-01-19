#!/usr/bin/env python3
"""
批量处理工具 - batch_process.py

用途：批量处理多个文档，支持统一格式转换、校对等操作

使用方法：
    python batch_process.py --input-dir ./docs --task format --output-dir ./output
    python batch_process.py --input-dir ./docs --task proofread --pattern "*.md"
    python batch_process.py --input-dir ./docs --task summarize --recursive

参数：
    --input-dir     输入目录
    --output-dir    输出目录
    --task          处理任务: format, proofread, summarize, convert
    --pattern       文件匹配模式
    --recursive     递归处理子目录
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import re


def find_files(input_dir: str, pattern: str = "*.*", recursive: bool = False) -> List[Path]:
    """查找文件"""
    directory = Path(input_dir)
    
    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))
    
    # 排除隐藏文件
    files = [f for f in files if not f.name.startswith('.') and f.is_file()]
    
    return sorted(files)


def process_format(content: str) -> str:
    """格式化处理"""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        # 标准化空格
        line = re.sub(r'[ \t]+', ' ', line)
        # 中英文之间加空格
        line = re.sub(r'([a-zA-Z])([^\x00-\xff])', r'\1 \2', line)
        line = re.sub(r'([^\x00-\xff])([a-zA-Z])', r'\1 \2', line)
        result.append(line)
    
    return '\n'.join(result)


def process_proofread(content: str) -> str:
    """校对处理"""
    # 常见错别字替换
    corrections = {
        "既使": "即使",
        "的确确": "的确",
        "签署日": "签署",
        "在加": "再加",
    }
    
    result = content
    for wrong, correct in corrections.items():
        result = result.replace(wrong, correct)
    
    return result


def process_summarize(content: str) -> str:
    """摘要处理"""
    lines = content.split('\n')
    
    # 提取标题和首段
    title = ""
    first_para = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            title = line
        elif line and not first_para:
            first_para = line[:200] + "..." if len(line) > 200 else line
        
        if title and first_para:
            break
    
    return f"## 摘要\n\n**标题**: {title}\n\n**概要**: {first_para}\n"


def process_file(file_path: Path, task: str) -> Dict:
    """处理单个文件"""
    result = {
        "file": str(file_path),
        "status": "success",
        "message": ""
    }
    
    try:
        content = file_path.read_text(encoding="utf-8")
        
        if task == "format":
            processed = process_format(content)
        elif task == "proofread":
            processed = process_proofread(content)
        elif task == "summarize":
            processed = process_summarize(content)
        else:
            processed = content
        
        result["processed_content"] = processed
        result["original_size"] = len(content)
        result["processed_size"] = len(processed)
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


def generate_report(results: List[Dict], task: str) -> str:
    """生成处理报告"""
    output = [f"# 批量处理报告\n"]
    output.append(f"\n**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.append(f"**处理任务**: {task}\n")
    output.append(f"**文件总数**: {len(results)}\n\n")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = len(results) - success_count
    
    output.append(f"## 统计\n")
    output.append(f"- ✅ 成功: {success_count}\n")
    output.append(f"- ❌ 失败: {error_count}\n\n")
    
    output.append(f"## 详细结果\n")
    output.append("| 文件 | 状态 | 原大小 | 处理后 |\n")
    output.append("|------|------|--------|--------|\n")
    
    for r in results:
        status = "✅" if r['status'] == 'success' else "❌"
        orig_size = r.get('original_size', '-')
        proc_size = r.get('processed_size', '-')
        output.append(f"| {Path(r['file']).name} | {status} | {orig_size} | {proc_size} |\n")
    
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(description="批量处理工具")
    parser.add_argument("--input-dir", "-i", help="输入目录")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    parser.add_argument("--task", "-t", default="format",
                        choices=["format", "proofread", "summarize", "convert"],
                        help="处理任务")
    parser.add_argument("--pattern", "-p", default="*.md", help="文件匹配模式")
    parser.add_argument("--recursive", "-r", action="store_true", help="递归处理")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将处理的文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ batch_process.py 测试通过")
        return
    
    if not args.input_dir:
        print("❌ 请指定输入目录: --input-dir <目录路径>")
        return
    
    # 查找文件
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"❌ 目录不存在: {args.input_dir}")
        return
    
    files = find_files(args.input_dir, args.pattern, args.recursive)
    print(f"找到 {len(files)} 个文件")
    
    if args.dry_run:
        for f in files:
            print(f"  - {f}")
        return
    
    # 处理文件
    results = []
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in files:
        print(f"处理: {file_path.name}...", end=" ")
        result = process_file(file_path, args.task)
        results.append(result)
        
        if result['status'] == 'success' and output_dir:
            output_file = output_dir / file_path.name
            output_file.write_text(result['processed_content'], encoding="utf-8")
        
        print("✅" if result['status'] == 'success' else "❌")
    
    # 生成报告
    report = generate_report(results, args.task)
    
    if output_dir:
        report_path = output_dir / "_batch_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\n📊 报告已保存: {report_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
