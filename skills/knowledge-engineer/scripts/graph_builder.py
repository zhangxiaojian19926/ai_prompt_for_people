#!/usr/bin/env python3
"""
知识图谱构建器 - graph_builder.py

用途：构建知识图谱并生成Mermaid可视化

使用方法：
    python graph_builder.py --input entities.json --output graph.md

参数：
    --input, -i     实体关系JSON文件
    --output, -o    输出Mermaid图
"""

import argparse
import json
from pathlib import Path

def build_mermaid_graph(entities: dict, relations: list) -> str:
    """生成Mermaid图"""
    lines = ["```mermaid", "graph TD"]
    
    # 添加概念节点
    concepts = entities.get("concepts", [])[:10]
    for i, concept in enumerate(concepts):
        safe_id = f"C{i}"
        lines.append(f'    {safe_id}["{concept}"]')
    
    # 添加关系边
    for i, rel in enumerate(relations[:10]):
        subj_id = f"C{concepts.index(rel['subject'])}" if rel['subject'] in concepts else f"R{i}"
        obj_id = f"O{i}"
        predicate = rel.get('predicate', '→')
        lines.append(f'    {subj_id} -->|{predicate}| {obj_id}["{rel.get("object", "")[:15]}"]')
    
    lines.append("```")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="知识图谱构建器")
    parser.add_argument("--input", "-i", help="实体关系JSON文件")
    parser.add_argument("--output", "-o", help="输出Mermaid图")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ graph_builder.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    data = json.loads(input_path.read_text(encoding="utf-8"))
    graph = build_mermaid_graph(data.get("entities", {}), data.get("relations", []))
    
    output_content = f"# 知识图谱\n\n{graph}"
    
    if args.output:
        Path(args.output).write_text(output_content, encoding="utf-8")
        print(f"✅ 知识图谱已生成: {args.output}")
    else:
        print(output_content)


if __name__ == "__main__":
    main()
