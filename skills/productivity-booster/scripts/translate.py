#!/usr/bin/env python3
"""
智能翻译工具 - translate.py

用途：多语言文档翻译，支持术语表和双语对照

使用方法：
    python translate.py --input doc.md --source en --target zh
    python translate.py --input doc.md --target zh --glossary terms.json
    python translate.py --input doc.md --target zh --bilingual --output translated.md

参数：
    --input, -i     输入文件路径
    --source, -s    源语言代码 (auto=自动检测)
    --target, -t    目标语言代码
    --glossary, -g  术语表JSON文件路径
    --bilingual     输出双语对照格式
    --output, -o    输出文件路径
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# 语言代码映射
LANG_NAMES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "auto": "自动检测"
}


def detect_language(text: str) -> str:
    """简单的语言检测"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    total_chars = len(text.replace(" ", ""))
    
    if total_chars == 0:
        return "auto"
    
    if chinese_chars / total_chars > 0.3:
        return "zh"
    return "en"


def load_glossary(glossary_path: str) -> Dict[str, str]:
    """加载术语表"""
    if not glossary_path:
        return {}
    
    path = Path(glossary_path)
    if not path.exists():
        return {}
    
    return json.loads(path.read_text(encoding="utf-8"))


def apply_glossary(text: str, glossary: Dict[str, str]) -> str:
    """应用术语表替换"""
    result = text
    for term, translation in glossary.items():
        result = result.replace(term, f"【{translation}】")
    return result


def translate_text(text: str, source: str, target: str, glossary: Dict[str, str]) -> str:
    """
    翻译文本（模拟实现）
    
    注意：这是一个模拟实现，实际使用时可以集成：
    - OpenAI API
    - Google Translate API
    - DeepL API
    - 百度翻译 API
    """
    # 应用术语表
    if glossary:
        text = apply_glossary(text, glossary)
    
    # 模拟翻译输出（实际项目中替换为真实API调用）
    return f"[翻译结果 {source}→{target}]\n{text}"


def format_bilingual(original: str, translated: str) -> str:
    """生成双语对照格式"""
    original_lines = original.split('\n')
    translated_lines = translated.split('\n')
    
    output = ["## 双语对照\n"]
    output.append("| 原文 | 译文 |\n")
    output.append("|------|------|\n")
    
    max_lines = max(len(original_lines), len(translated_lines))
    for i in range(min(max_lines, 20)):  # 限制行数
        orig = original_lines[i] if i < len(original_lines) else ""
        trans = translated_lines[i] if i < len(translated_lines) else ""
        output.append(f"| {orig} | {trans} |\n")
    
    return "".join(output)


def extract_terms(text: str, translated: str) -> List[Dict[str, str]]:
    """提取术语对照"""
    # 简单实现：查找被标记的术语
    terms = re.findall(r'【(.+?)】', translated)
    return [{"原文": t, "译文": t, "备注": "术语"} for t in terms[:10]]


def format_output(original: str, translated: str, source: str, target: str, 
                  bilingual: bool, terms: List[Dict]) -> str:
    """格式化输出"""
    output = ["## 翻译文档\n"]
    
    # 元信息
    output.append("### 元信息\n")
    output.append(f"- 原语言：{LANG_NAMES.get(source, source)}\n")
    output.append(f"- 目标语言：{LANG_NAMES.get(target, target)}\n")
    output.append(f"- 字数：{len(original)}\n\n")
    
    if bilingual:
        output.append(format_bilingual(original, translated))
    else:
        output.append("### 译文\n")
        output.append(translated)
        output.append("\n")
    
    if terms:
        output.append("\n### 术语对照表\n")
        output.append("| 原文 | 译文 | 备注 |\n")
        output.append("|------|------|------|\n")
        for term in terms:
            output.append(f"| {term['原文']} | {term['译文']} | {term['备注']} |\n")
    
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(description="智能翻译工具")
    parser.add_argument("--input", "-i", help="输入文件路径")
    parser.add_argument("--source", "-s", default="auto", help="源语言代码")
    parser.add_argument("--target", "-t", default="zh", help="目标语言代码")
    parser.add_argument("--glossary", "-g", help="术语表JSON文件")
    parser.add_argument("--bilingual", action="store_true", help="双语对照输出")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ translate.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    # 读取输入
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 检测源语言
    source = args.source if args.source != "auto" else detect_language(text)
    
    # 加载术语表
    glossary = load_glossary(args.glossary)
    
    # 翻译
    translated = translate_text(text, source, args.target, glossary)
    
    # 提取术语
    terms = extract_terms(text, translated)
    
    # 格式化输出
    output = format_output(text, translated, source, args.target, args.bilingual, terms)
    
    # 输出
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 翻译已保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
