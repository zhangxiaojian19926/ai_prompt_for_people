#!/usr/bin/env python3
"""
增强版PDF转换器 - pdf_converter.py

基于Anthropic官方PDF技能最佳实践，集成多种工具实现高质量PDF转Markdown

使用方法：
    # 基础转换（自动选择最佳方法）
    python pdf_converter.py --input document.pdf --output output.md

    # 扫描版PDF（使用OCR）
    python pdf_converter.py --input scanned.pdf --output output.md --ocr

    # 提取表格
    python pdf_converter.py --input document.pdf --output output.md --tables

    # 高精度模式（速度较慢但质量更高）
    python pdf_converter.py --input document.pdf --output output.md --hq

    # 指定页面范围
    python pdf_converter.py --input document.pdf --output output.md --pages 1-5

依赖安装：
    pip install pypdf pdfplumber pypdfium2 pytesseract pdf2image pillow

系统依赖（macOS）：
    brew install poppler tesseract tesseract-lang
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import json

# 尝试导入依赖
DEPENDENCIES = {
    "pypdf": False,
    "pdfplumber": False,
    "pypdfium2": False,
    "pytesseract": False,
    "pdf2image": False,
    "PIL": False
}

try:
    from pypdf import PdfReader
    DEPENDENCIES["pypdf"] = True
except ImportError:
    pass

try:
    import pdfplumber
    DEPENDENCIES["pdfplumber"] = True
except ImportError:
    pass

try:
    import pypdfium2 as pdfium
    DEPENDENCIES["pypdfium2"] = True
except ImportError:
    pass

try:
    import pytesseract
    DEPENDENCIES["pytesseract"] = True
except ImportError:
    pass

try:
    from pdf2image import convert_from_path
    DEPENDENCIES["pdf2image"] = True
except ImportError:
    pass

try:
    from PIL import Image
    DEPENDENCIES["PIL"] = True
except ImportError:
    pass


def check_dependencies():
    """检查依赖状态"""
    print("📦 依赖检查:")
    for dep, status in DEPENDENCIES.items():
        status_str = "✅" if status else "❌"
        print(f"  {status_str} {dep}")
    
    missing = [k for k, v in DEPENDENCIES.items() if not v]
    if missing:
        print(f"\n⚠️ 缺失依赖: {', '.join(missing)}")
        print("安装命令: pip install pypdf pdfplumber pypdfium2 pytesseract pdf2image pillow")
    return len(missing) == 0


def extract_text_pypdf(pdf_path: str, pages: Optional[List[int]] = None) -> str:
    """使用pypdf提取文本（适合文本型PDF）"""
    if not DEPENDENCIES["pypdf"]:
        return ""
    
    reader = PdfReader(pdf_path)
    text_parts = []
    
    page_range = pages or range(len(reader.pages))
    for i in page_range:
        if i < len(reader.pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text_parts.append(f"\n## 第 {i+1} 页\n\n{page_text}")
    
    return "\n".join(text_parts)


def extract_text_pdfplumber(pdf_path: str, pages: Optional[List[int]] = None) -> Tuple[str, List[str]]:
    """使用pdfplumber提取文本和表格（推荐方法）"""
    if not DEPENDENCIES["pdfplumber"]:
        return "", []
    
    text_parts = []
    tables_md = []
    
    with pdfplumber.open(pdf_path) as pdf:
        page_range = pages or range(len(pdf.pages))
        for i in page_range:
            if i < len(pdf.pages):
                page = pdf.pages[i]
                
                # 提取文本
                text = page.extract_text()
                if text:
                    text_parts.append(f"\n## 第 {i+1} 页\n\n{text}")
                
                # 提取表格
                tables = page.extract_tables()
                for j, table in enumerate(tables):
                    if table and len(table) > 0:
                        table_md = table_to_markdown(table)
                        tables_md.append(f"### 第 {i+1} 页 - 表格 {j+1}\n\n{table_md}")
    
    return "\n".join(text_parts), tables_md


def table_to_markdown(table: list) -> str:
    """将表格转换为Markdown格式"""
    if not table or len(table) == 0:
        return ""
    
    # 清理表格数据
    cleaned = []
    for row in table:
        cleaned_row = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        cleaned.append(cleaned_row)
    
    if len(cleaned) == 0:
        return ""
    
    # 生成Markdown表格
    lines = []
    header = cleaned[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    
    for row in cleaned[1:]:
        # 确保行长度与表头一致
        while len(row) < len(header):
            row.append("")
        lines.append("| " + " | ".join(row[:len(header)]) + " |")
    
    return "\n".join(lines)


def extract_text_ocr(pdf_path: str, pages: Optional[List[int]] = None, lang: str = "chi_sim+eng") -> str:
    """使用OCR提取扫描版PDF文本"""
    if not (DEPENDENCIES["pytesseract"] and DEPENDENCIES["pdf2image"]):
        print("❌ OCR需要安装 pytesseract 和 pdf2image")
        return ""
    
    text_parts = []
    
    try:
        # 转换PDF为图像
        images = convert_from_path(pdf_path, dpi=300)
        
        page_range = pages or range(len(images))
        for i in page_range:
            if i < len(images):
                print(f"  OCR处理第 {i+1}/{len(images)} 页...")
                
                # OCR识别
                text = pytesseract.image_to_string(images[i], lang=lang)
                if text.strip():
                    text_parts.append(f"\n## 第 {i+1} 页\n\n{text}")
    
    except Exception as e:
        print(f"❌ OCR处理失败: {e}")
        return ""
    
    return "\n".join(text_parts)


def render_pdf_to_images(pdf_path: str, output_dir: str, scale: float = 2.0) -> List[str]:
    """渲染PDF为图像（使用pypdfium2）"""
    if not DEPENDENCIES["pypdfium2"]:
        print("⚠️ pypdfium2未安装，尝试使用pdf2image...")
        return render_pdf_to_images_fallback(pdf_path, output_dir)
    
    image_paths = []
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        for i, page in enumerate(pdf):
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()
            img_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
            img.save(img_path, "PNG")
            image_paths.append(img_path)
            print(f"  渲染第 {i+1}/{len(pdf)} 页...")
    except Exception as e:
        print(f"❌ 渲染失败: {e}")
    
    return image_paths


def render_pdf_to_images_fallback(pdf_path: str, output_dir: str) -> List[str]:
    """使用pdf2image作为后备方案"""
    if not DEPENDENCIES["pdf2image"]:
        return []
    
    image_paths = []
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        images = convert_from_path(pdf_path, dpi=200)
        for i, img in enumerate(images):
            img_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
            img.save(img_path, "PNG")
            image_paths.append(img_path)
    except Exception as e:
        print(f"❌ 渲染失败: {e}")
    
    return image_paths


def analyze_pdf(pdf_path: str) -> dict:
    """分析PDF特征，选择最佳处理方法"""
    info = {
        "pages": 0,
        "has_text": False,
        "has_images": False,
        "is_scanned": False,
        "has_tables": False,
        "recommended_method": "pdfplumber"
    }
    
    if DEPENDENCIES["pypdf"]:
        try:
            reader = PdfReader(pdf_path)
            info["pages"] = len(reader.pages)
            
            # 检查前几页是否有文本
            sample_text = ""
            for i in range(min(3, len(reader.pages))):
                text = reader.pages[i].extract_text() or ""
                sample_text += text
            
            info["has_text"] = len(sample_text.strip()) > 100
            info["is_scanned"] = not info["has_text"]
            
        except Exception as e:
            print(f"⚠️ 分析失败: {e}")
    
    if DEPENDENCIES["pdfplumber"]:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:3]:
                    tables = page.extract_tables()
                    if tables:
                        info["has_tables"] = True
                        break
        except:
            pass
    
    # 推荐方法
    if info["is_scanned"]:
        info["recommended_method"] = "ocr"
    elif info["has_tables"]:
        info["recommended_method"] = "pdfplumber"
    else:
        info["recommended_method"] = "pdfplumber"
    
    return info


def generate_markdown(pdf_path: str, text: str, tables: List[str], images_dir: Optional[str] = None) -> str:
    """生成最终的Markdown文档"""
    pdf_name = Path(pdf_path).stem
    
    output = f"""# {pdf_name}

**源文件**: {Path(pdf_path).name}
**转换日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**转换工具**: pdf_converter.py (基于Anthropic最佳实践)

---

## 目录

[TOC]

---

{text}
"""
    
    if tables:
        output += "\n\n---\n\n## 表格汇总\n\n"
        output += "\n\n".join(tables)
    
    if images_dir and os.path.exists(images_dir):
        output += "\n\n---\n\n## 页面图像\n\n"
        for img_file in sorted(os.listdir(images_dir)):
            if img_file.endswith(('.png', '.jpg')):
                output += f"![{img_file}]({images_dir}/{img_file})\n\n"
    
    return output


def convert_pdf(pdf_path: str, output_path: str, options: dict) -> bool:
    """主转换函数"""
    print(f"\n📄 处理: {pdf_path}")
    
    # 分析PDF
    print("🔍 分析PDF...")
    info = analyze_pdf(pdf_path)
    print(f"  - 页数: {info['pages']}")
    print(f"  - 文本型: {'是' if info['has_text'] else '否'}")
    print(f"  - 扫描版: {'是' if info['is_scanned'] else '否'}")
    print(f"  - 包含表格: {'是' if info['has_tables'] else '否'}")
    print(f"  - 推荐方法: {info['recommended_method']}")
    
    # 解析页面范围
    pages = None
    if options.get("pages"):
        pages = parse_page_range(options["pages"], info["pages"])
    
    text = ""
    tables = []
    
    # 选择处理方法
    method = options.get("method") or info["recommended_method"]
    
    if options.get("ocr") or method == "ocr":
        print("🔤 OCR识别中...")
        text = extract_text_ocr(pdf_path, pages, options.get("lang", "chi_sim+eng"))
    else:
        print("📝 提取文本...")
        if options.get("tables") or info["has_tables"]:
            text, tables = extract_text_pdfplumber(pdf_path, pages)
        else:
            text, tables = extract_text_pdfplumber(pdf_path, pages)
    
    # 如果文本提取失败，尝试OCR
    if not text.strip() and not options.get("no_fallback"):
        print("⚠️ 文本提取失败，尝试OCR...")
        text = extract_text_ocr(pdf_path, pages)
    
    # 渲染图像（如果请求）
    images_dir = None
    if options.get("images"):
        output_dir = Path(output_path).parent / "images"
        print(f"🖼️ 渲染图像到 {output_dir}...")
        render_pdf_to_images(pdf_path, str(output_dir))
        images_dir = "images"
    
    # 生成Markdown
    print("📝 生成Markdown...")
    markdown = generate_markdown(pdf_path, text, tables, images_dir)
    
    # 保存
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(markdown, encoding="utf-8")
    
    print(f"✅ 已保存: {output_path}")
    print(f"   文本字数: {len(text)}")
    print(f"   表格数量: {len(tables)}")
    
    return True


def parse_page_range(page_str: str, total_pages: int) -> List[int]:
    """解析页面范围字符串"""
    pages = []
    for part in page_str.split(","):
        if "-" in part:
            start, end = part.split("-")
            pages.extend(range(int(start)-1, min(int(end), total_pages)))
        else:
            pages.append(int(part) - 1)
    return [p for p in pages if 0 <= p < total_pages]


def main():
    parser = argparse.ArgumentParser(
        description="增强版PDF转Markdown转换器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python pdf_converter.py --input doc.pdf --output doc.md
    python pdf_converter.py --input scanned.pdf --output doc.md --ocr
    python pdf_converter.py --input doc.pdf --output doc.md --tables --images
        """
    )
    
    parser.add_argument("--input", "-i", help="输入PDF文件")
    parser.add_argument("--output", "-o", help="输出Markdown文件")
    parser.add_argument("--ocr", action="store_true", help="使用OCR（适合扫描版）")
    parser.add_argument("--tables", action="store_true", help="提取表格")
    parser.add_argument("--images", action="store_true", help="同时渲染页面图像")
    parser.add_argument("--pages", help="页面范围，如: 1-5 或 1,3,5")
    parser.add_argument("--lang", default="chi_sim+eng", help="OCR语言")
    parser.add_argument("--hq", action="store_true", help="高质量模式")
    parser.add_argument("--check-deps", action="store_true", help="检查依赖")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ pdf_converter.py 测试通过")
        return
    
    if args.check_deps:
        check_dependencies()
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <PDF文件>")
        parser.print_help()
        return
    
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        return
    
    # 默认输出路径
    output_path = args.output or args.input.replace(".pdf", ".md")
    
    options = {
        "ocr": args.ocr,
        "tables": args.tables,
        "images": args.images,
        "pages": args.pages,
        "lang": args.lang,
        "hq": args.hq
    }
    
    convert_pdf(args.input, output_path, options)


if __name__ == "__main__":
    main()
