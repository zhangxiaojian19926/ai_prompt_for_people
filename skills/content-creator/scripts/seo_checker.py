#!/usr/bin/env python3
"""
SEO检查工具 - seo_checker.py

用途：检查文章SEO优化情况，生成优化报告

使用方法：
    python seo_checker.py --input article.md --keyword "目标关键词" --output report.md
    python seo_checker.py --input article.md --verbose

参数：
    --input, -i     输入文章文件
    --keyword, -k   目标关键词
    --output, -o    输出报告文件
    --verbose, -v   详细输出
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple


def extract_title(text: str) -> str:
    """提取标题"""
    match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    return match.group(1) if match else ""


def extract_meta_description(text: str) -> str:
    """提取描述（取首段或blockquote）"""
    # 查找blockquote
    match = re.search(r'^\>\s+(.+)$', text, re.MULTILINE)
    if match:
        return match.group(1)
    
    # 取首段
    paragraphs = re.split(r'\n\s*\n', text)
    for p in paragraphs:
        if not p.startswith('#') and len(p.strip()) > 20:
            return p.strip()[:160]
    
    return ""


def count_headings(text: str) -> Dict[str, int]:
    """统计标题层级"""
    return {
        "h1": len(re.findall(r'^# ', text, re.MULTILINE)),
        "h2": len(re.findall(r'^## ', text, re.MULTILINE)),
        "h3": len(re.findall(r'^### ', text, re.MULTILINE)),
        "h4": len(re.findall(r'^#### ', text, re.MULTILINE)),
    }


def count_keyword(text: str, keyword: str) -> Dict[str, any]:
    """统计关键词"""
    if not keyword:
        return {"count": 0, "density": 0, "in_title": False, "in_headings": False}
    
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    
    count = text_lower.count(keyword_lower)
    word_count = len(text.split())
    density = (count / max(1, word_count)) * 100
    
    # 检查标题
    title = extract_title(text)
    in_title = keyword_lower in title.lower()
    
    # 检查副标题
    headings = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
    in_headings = any(keyword_lower in h.lower() for h in headings)
    
    return {
        "count": count,
        "density": round(density, 2),
        "in_title": in_title,
        "in_headings": in_headings
    }


def check_links(text: str) -> Dict[str, int]:
    """检查链接"""
    internal_links = len(re.findall(r'\[.+?\]\((?!http).+?\)', text))
    external_links = len(re.findall(r'\[.+?\]\(https?://.+?\)', text))
    
    return {
        "internal": internal_links,
        "external": external_links,
        "total": internal_links + external_links
    }


def check_images(text: str) -> Dict[str, any]:
    """检查图片"""
    images = re.findall(r'!\[(.+?)\]\((.+?)\)', text)
    
    has_alt = sum(1 for alt, _ in images if alt.strip())
    no_alt = len(images) - has_alt
    
    return {
        "total": len(images),
        "with_alt": has_alt,
        "without_alt": no_alt
    }


def calculate_score(checks: Dict) -> int:
    """计算SEO分数"""
    score = 0
    
    # 标题检查 (20分)
    if checks["title"]:
        score += 10
    if checks["keyword"]["in_title"]:
        score += 10
    
    # 结构检查 (20分)
    if checks["headings"]["h1"] == 1:
        score += 10
    if checks["headings"]["h2"] >= 2:
        score += 10
    
    # 关键词检查 (20分)
    if 0.5 <= checks["keyword"]["density"] <= 2.5:
        score += 10
    if checks["keyword"]["in_headings"]:
        score += 10
    
    # 链接检查 (20分)
    if checks["links"]["internal"] > 0:
        score += 10
    if checks["links"]["external"] > 0:
        score += 10
    
    # 字数检查 (10分)
    if checks["word_count"] >= 500:
        score += 10
    
    # 图片检查 (10分)
    if checks["images"]["total"] > 0 and checks["images"]["without_alt"] == 0:
        score += 10
    
    return score


def generate_suggestions(checks: Dict) -> List[str]:
    """生成优化建议"""
    suggestions = []
    
    if not checks["keyword"]["in_title"]:
        suggestions.append("建议在标题中包含目标关键词")
    
    if checks["headings"]["h1"] != 1:
        suggestions.append(f"H1标题应该唯一（当前{checks['headings']['h1']}个）")
    
    if checks["headings"]["h2"] < 2:
        suggestions.append("建议增加更多H2副标题来组织内容")
    
    if checks["keyword"]["density"] < 0.5:
        suggestions.append("关键词密度偏低，建议适当增加关键词出现次数")
    elif checks["keyword"]["density"] > 2.5:
        suggestions.append("关键词密度偏高，可能被判定为关键词堆砌")
    
    if checks["links"]["internal"] == 0:
        suggestions.append("建议添加内部链接提高页面关联性")
    
    if checks["links"]["external"] == 0:
        suggestions.append("建议添加权威外部链接增加可信度")
    
    if checks["images"]["without_alt"] > 0:
        suggestions.append(f"有{checks['images']['without_alt']}张图片缺少alt标签")
    
    if checks["word_count"] < 500:
        suggestions.append("文章字数偏少，建议增加内容深度")
    
    return suggestions


def format_report(checks: Dict, score: int, suggestions: List[str]) -> str:
    """格式化报告"""
    output = ["# SEO优化报告\n"]
    output.append(f"**检查时间**: {checks['timestamp']}")
    output.append(f"**目标关键词**: {checks['keyword_input'] or '未指定'}")
    output.append(f"**SEO评分**: {score}/100\n")
    
    # 评级
    if score >= 80:
        grade = "优秀 ✅"
    elif score >= 60:
        grade = "良好 🟡"
    elif score >= 40:
        grade = "待改进 🟠"
    else:
        grade = "较差 ❌"
    output.append(f"**评级**: {grade}\n")
    
    # 基本信息
    output.append("## 基本信息\n")
    output.append(f"- 标题：{checks['title'] or '❌ 未找到'}")
    output.append(f"- 字数：{checks['word_count']}")
    output.append(f"- 描述（前160字）：{checks['description'][:80]}...\n")
    
    # 结构分析
    output.append("## 结构分析\n")
    output.append(f"| 标题层级 | 数量 |")
    output.append(f"|----------|------|")
    for level, count in checks['headings'].items():
        output.append(f"| {level.upper()} | {count} |")
    output.append("")
    
    # 关键词分析
    output.append("## 关键词分析\n")
    kw = checks['keyword']
    output.append(f"- 出现次数：{kw['count']}")
    output.append(f"- 关键词密度：{kw['density']}%")
    output.append(f"- 标题包含：{'✅' if kw['in_title'] else '❌'}")
    output.append(f"- 副标题包含：{'✅' if kw['in_headings'] else '❌'}\n")
    
    # 链接分析
    output.append("## 链接分析\n")
    output.append(f"- 内部链接：{checks['links']['internal']}")
    output.append(f"- 外部链接：{checks['links']['external']}\n")
    
    # 图片分析
    output.append("## 图片分析\n")
    output.append(f"- 图片总数：{checks['images']['total']}")
    output.append(f"- 有alt标签：{checks['images']['with_alt']}")
    output.append(f"- 缺少alt：{checks['images']['without_alt']}\n")
    
    # 优化建议
    if suggestions:
        output.append("## 优化建议\n")
        for i, s in enumerate(suggestions, 1):
            output.append(f"{i}. {s}")
    else:
        output.append("## 优化建议\n")
        output.append("✅ SEO表现良好，无明显问题")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="SEO检查工具")
    parser.add_argument("--input", "-i", help="输入文章文件")
    parser.add_argument("--keyword", "-k", help="目标关键词")
    parser.add_argument("--output", "-o", help="输出报告文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ seo_checker.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 执行检查
    from datetime import datetime
    checks = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "keyword_input": args.keyword or "",
        "title": extract_title(text),
        "description": extract_meta_description(text),
        "word_count": len(text.split()),
        "headings": count_headings(text),
        "keyword": count_keyword(text, args.keyword or ""),
        "links": check_links(text),
        "images": check_images(text)
    }
    
    # 计算分数
    score = calculate_score(checks)
    
    # 生成建议
    suggestions = generate_suggestions(checks)
    
    # 格式化报告
    report = format_report(checks, score, suggestions)
    
    # 输出
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ SEO报告已保存到: {args.output}")
        print(f"   评分: {score}/100")
    else:
        print(report)


if __name__ == "__main__":
    main()
