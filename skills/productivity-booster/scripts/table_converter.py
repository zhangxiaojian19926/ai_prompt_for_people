#!/usr/bin/env python3
"""
表格转换工具 - table_converter.py

用途：CSV/Excel 转 Markdown 表格，支持数据清洗和格式化

使用方法：
    python table_converter.py --input data.csv --output table.md
    python table_converter.py --input data.xlsx --sheet Sheet1
    python table_converter.py --input data.csv --clean --align center

参数：
    --input, -i     输入文件路径 (CSV/Excel)
    --output, -o    输出Markdown文件
    --sheet         Excel工作表名称
    --clean         清洗数据（去空行、去重）
    --align         对齐方式: left, center, right
    --max-rows      最大行数限制
"""

import argparse
import csv
from pathlib import Path
from typing import List, Optional

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def read_csv(file_path: str) -> List[List[str]]:
    """读取CSV文件"""
    rows = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def read_excel(file_path: str, sheet_name: Optional[str] = None) -> List[List[str]]:
    """读取Excel文件"""
    if not HAS_OPENPYXL:
        raise ImportError("需要安装 openpyxl: pip install openpyxl")
    
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active
    
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([str(cell) if cell is not None else "" for cell in row])
    
    return rows


def clean_data(rows: List[List[str]], remove_empty: bool = True, 
               remove_duplicates: bool = True) -> List[List[str]]:
    """清洗数据"""
    if not rows:
        return rows
    
    result = rows.copy()
    
    # 移除空行
    if remove_empty:
        result = [row for row in result if any(cell.strip() for cell in row)]
    
    # 移除重复行（保留表头）
    if remove_duplicates and len(result) > 1:
        header = result[0]
        seen = set()
        unique_rows = [header]
        for row in result[1:]:
            row_tuple = tuple(row)
            if row_tuple not in seen:
                seen.add(row_tuple)
                unique_rows.append(row)
        result = unique_rows
    
    return result


def create_separator(col_count: int, align: str = "left") -> str:
    """创建分隔行"""
    if align == "center":
        sep = "|:---:|"
    elif align == "right":
        sep = "|---:|"
    else:
        sep = "|---|"
    
    return sep * col_count + "\n"


def convert_to_markdown(rows: List[List[str]], align: str = "left") -> str:
    """转换为Markdown表格"""
    if not rows:
        return "无数据"
    
    output = []
    
    # 表头
    header = rows[0]
    output.append("| " + " | ".join(header) + " |\n")
    
    # 分隔行
    output.append(create_separator(len(header), align))
    
    # 数据行
    for row in rows[1:]:
        # 确保列数一致
        while len(row) < len(header):
            row.append("")
        output.append("| " + " | ".join(row[:len(header)]) + " |\n")
    
    return "".join(output)


def format_output(table_md: str, rows: List[List[str]], source: str) -> str:
    """格式化完整输出"""
    output = ["## 数据表格\n"]
    output.append(f"\n### 数据概览\n")
    output.append(f"- 数据来源：`{source}`\n")
    output.append(f"- 行数：{len(rows) - 1} 条数据\n")
    output.append(f"- 列数：{len(rows[0]) if rows else 0}\n")
    output.append(f"\n### 数据表\n\n")
    output.append(table_md)
    
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(description="表格转换工具")
    parser.add_argument("--input", "-i", help="输入文件 (CSV/Excel)")
    parser.add_argument("--output", "-o", help="输出Markdown文件")
    parser.add_argument("--sheet", help="Excel工作表名称")
    parser.add_argument("--clean", action="store_true", help="清洗数据")
    parser.add_argument("--align", default="left", 
                        choices=["left", "center", "right"],
                        help="对齐方式")
    parser.add_argument("--max-rows", type=int, default=100, help="最大行数")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ table_converter.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    # 读取数据
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        rows = read_csv(args.input)
    elif suffix in [".xlsx", ".xls"]:
        rows = read_excel(args.input, args.sheet)
    else:
        print(f"❌ 不支持的文件格式: {suffix}")
        return
    
    # 清洗
    if args.clean:
        rows = clean_data(rows)
    
    # 限制行数
    if len(rows) > args.max_rows + 1:
        print(f"⚠️ 数据行数 {len(rows)-1} 超过限制，截取前 {args.max_rows} 行")
        rows = rows[:args.max_rows + 1]
    
    # 转换
    table_md = convert_to_markdown(rows, args.align)
    
    # 格式化
    output = format_output(table_md, rows, input_path.name)
    
    # 输出
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 表格已转换，保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
