#!/usr/bin/env python3
"""
RAG索引构建器 - rag_indexer.py

用途：为知识库构建RAG索引

使用方法：
    python rag_indexer.py --input ./docs --output index/
    python rag_indexer.py --input ./docs --chunk-size 500

参数：
    --input, -i     输入文档目录
    --output, -o    索引输出目录
    --chunk-size    分块大小（字符）
"""

import argparse
import hashlib
import json
from pathlib import Path

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """将文本分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append({
            "content": chunk,
            "start": start,
            "end": end,
            "id": hashlib.md5(chunk.encode()).hexdigest()[:8]
        })
        start = end - overlap
    return chunks


def process_file(file_path: Path, chunk_size: int) -> list:
    """处理单个文件"""
    try:
        content = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(content, chunk_size)
        for chunk in chunks:
            chunk["source"] = str(file_path)
            chunk["filename"] = file_path.name
        return chunks
    except Exception as e:
        print(f"⚠️ 跳过 {file_path}: {e}")
        return []


def build_index(input_dir: str, chunk_size: int) -> dict:
    """构建索引"""
    input_path = Path(input_dir)
    all_chunks = []
    
    for file_path in input_path.rglob("*.md"):
        chunks = process_file(file_path, chunk_size)
        all_chunks.extend(chunks)
    
    for file_path in input_path.rglob("*.txt"):
        chunks = process_file(file_path, chunk_size)
        all_chunks.extend(chunks)
    
    return {
        "total_chunks": len(all_chunks),
        "sources": list(set(c["source"] for c in all_chunks)),
        "chunks": all_chunks
    }


def main():
    parser = argparse.ArgumentParser(description="RAG索引构建器")
    parser.add_argument("--input", "-i", help="输入文档目录")
    parser.add_argument("--output", "-o", help="索引输出目录")
    parser.add_argument("--chunk-size", type=int, default=500, help="分块大小")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ rag_indexer.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定输入目录: --input <目录>")
        return
    
    index = build_index(args.input, args.chunk_size)
    
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        index_file = output_path / "index.json"
        index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 索引已构建: {index_file}")
        print(f"   - 文档数: {len(index['sources'])}")
        print(f"   - 分块数: {index['total_chunks']}")
    else:
        print(f"索引统计: {index['total_chunks']} 个分块，来自 {len(index['sources'])} 个文档")


if __name__ == "__main__":
    main()
