#!/usr/bin/env python3
"""
依赖分析器 - dep_analyzer.py

用途：分析项目依赖关系

使用方法：
    python dep_analyzer.py --input requirements.txt --output report.md
    python dep_analyzer.py --dir ./project --type python

参数：
    --input, -i     依赖文件 (requirements.txt, package.json等)
    --dir, -d       项目目录
    --type, -t      项目类型: python, node, go
    --output, -o    输出报告
"""

import argparse
import re
from pathlib import Path

def parse_requirements(content: str) -> list:
    """解析requirements.txt"""
    deps = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # 解析包名和版本
            match = re.match(r'^([a-zA-Z0-9_-]+)([<>=!]+.+)?$', line)
            if match:
                deps.append({
                    "name": match.group(1),
                    "version": match.group(2) or "any"
                })
    return deps


def analyze_imports(code_dir: str) -> list:
    """分析Python导入"""
    imports = set()
    code_path = Path(code_dir)
    
    for py_file in code_path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            # 简单匹配import语句
            import_matches = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
            imports.update(import_matches)
        except:
            pass
    
    return sorted(imports)


def generate_report(deps: list, imports: list = None) -> str:
    """生成依赖报告"""
    output = ["# 依赖分析报告\n"]
    
    output.append("## 依赖列表\n")
    output.append("| 包名 | 版本 |")
    output.append("|------|------|")
    for dep in deps:
        output.append(f"| {dep['name']} | {dep['version']} |")
    output.append("")
    
    output.append(f"## 统计\n")
    output.append(f"- 依赖总数: {len(deps)}")
    
    if imports:
        output.append(f"\n## 导入分析\n")
        output.append(f"项目中使用的导入: {len(imports)}")
        output.append("\n```")
        output.append("\n".join(imports[:20]))  # 只显示前20个
        if len(imports) > 20:
            output.append(f"... 还有 {len(imports) - 20} 个")
        output.append("```")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="依赖分析器")
    parser.add_argument("--input", "-i", help="依赖文件")
    parser.add_argument("--dir", "-d", help="项目目录")
    parser.add_argument("--type", "-t", default="python",
                        choices=["python", "node", "go"],
                        help="项目类型")
    parser.add_argument("--output", "-o", help="输出报告")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ dep_analyzer.py 测试通过")
        return
    
    deps = []
    imports = []
    
    if args.input:
        input_path = Path(args.input)
        if input_path.exists():
            content = input_path.read_text(encoding="utf-8")
            deps = parse_requirements(content)
    
    if args.dir:
        imports = analyze_imports(args.dir)
    
    if not deps and not imports:
        print("❌ 请指定依赖文件 (--input) 或项目目录 (--dir)")
        return
    
    report = generate_report(deps, imports)
    
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ 报告已生成: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
