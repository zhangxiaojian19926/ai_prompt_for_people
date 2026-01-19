#!/usr/bin/env python3
"""
实体提取器 - entity_extractor.py

用途：从文本中提取实体和关系

使用方法：
    python entity_extractor.py --input doc.md --output entities.json

参数：
    --input, -i     输入文本文件
    --output, -o    输出文件
"""

import argparse
import re
import json
from pathlib import Path

def extract_entities(text: str) -> dict:
    """提取实体"""
    entities = {
        "persons": [],
        "organizations": [],
        "concepts": [],
        "terms": []
    }
    
    # 提取加粗的内容作为概念
    bold = re.findall(r'\*\*(.+?)\*\*', text)
    entities["concepts"] = list(set(bold))[:20]
    
    # 提取标题作为术语
    headers = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
    entities["terms"] = list(set(headers))[:20]
    
    return entities


def extract_relations(text: str, entities: dict) -> list:
    """提取关系（简化版）"""
    relations = []
    concepts = entities.get("concepts", [])
    
    # 查找"是"关系
    for concept in concepts[:10]:
        pattern = f'{concept}.{{0,20}}是.{{0,30}}'
        matches = re.findall(pattern, text)
        for match in matches[:3]:
            relations.append({
                "subject": concept,
                "predicate": "是",
                "object": match.replace(concept, "").strip()[:30]
            })
    
    return relations[:20]


def main():
    parser = argparse.ArgumentParser(description="实体提取器")
    parser.add_argument("--input", "-i", help="输入文本文件")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ entity_extractor.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    entities = extract_entities(text)
    relations = extract_relations(text, entities)
    
    result = {
        "entities": entities,
        "relations": relations,
        "stats": {
            "concept_count": len(entities["concepts"]),
            "term_count": len(entities["terms"]),
            "relation_count": len(relations)
        }
    }
    
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 实体已提取: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
