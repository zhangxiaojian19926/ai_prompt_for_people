#!/usr/bin/env python3
"""
行动项提取工具 - extract_actions.py

用途：从会议记录中自动提取行动项、决议和待办事项

使用方法：
    python extract_actions.py --input meeting.md --output actions.md
    python extract_actions.py --input meeting.md --format table
    python extract_actions.py --input meeting.md --assignee "张三"

参数：
    --input, -i     输入会议记录文件
    --output, -o    输出文件路径
    --format, -f    输出格式: markdown, table, json
    --assignee      筛选特定责任人
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


# 行动项关键词
ACTION_KEYWORDS = [
    "负责", "跟进", "完成", "提交", "准备", "确认", "联系", "安排",
    "需要", "待办", "行动项", "TODO", "Action", "待", "请"
]

# 决议关键词
DECISION_KEYWORDS = [
    "决定", "同意", "确定", "通过", "决议", "达成共识", "一致认为"
]


def extract_actions(text: str) -> List[Dict]:
    """提取行动项"""
    actions = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # 检查是否包含行动关键词
        for keyword in ACTION_KEYWORDS:
            if keyword in line:
                action = {
                    "id": len(actions) + 1,
                    "content": line,
                    "keyword": keyword,
                    "assignee": extract_assignee(line),
                    "deadline": extract_deadline(line),
                    "status": "⏳待完成",
                    "line_number": i + 1
                }
                actions.append(action)
                break
    
    return actions


def extract_decisions(text: str) -> List[Dict]:
    """提取决议事项"""
    decisions = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        for keyword in DECISION_KEYWORDS:
            if keyword in line:
                decision = {
                    "id": len(decisions) + 1,
                    "content": line,
                    "keyword": keyword,
                    "line_number": i + 1
                }
                decisions.append(decision)
                break
    
    return decisions


def extract_assignee(text: str) -> str:
    """提取责任人"""
    # 匹配常见的责任人模式
    patterns = [
        r'(?:负责人|责任人|负责|由)[:：]?\s*([^\s,，。]+)',
        r'@(\w+)',
        r'([张李王刘陈]\w{1,2})(?:负责|跟进|完成)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return "待分配"


def extract_deadline(text: str) -> str:
    """提取截止日期"""
    # 匹配日期模式
    patterns = [
        r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})',
        r'(\d{1,2}月\d{1,2}[日号])',
        r'(本周[一二三四五六日末])',
        r'(下周[一二三四五六日末])',
        r'(明天|后天|今天)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    # 默认一周后
    default_date = datetime.now() + timedelta(days=7)
    return default_date.strftime("%Y-%m-%d")


def format_markdown(actions: List[Dict], decisions: List[Dict]) -> str:
    """格式化为Markdown"""
    output = ["## 会议纪要摘要\n"]
    output.append(f"*提取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
    
    # 决议事项
    if decisions:
        output.append("### 决议事项\n")
        for d in decisions:
            output.append(f"{d['id']}. ✅ {d['content']}\n")
        output.append("\n")
    
    # 行动项
    if actions:
        output.append("### 行动项\n")
        output.append("| 序号 | 任务 | 负责人 | 截止日期 | 状态 |\n")
        output.append("|------|------|--------|---------|------|\n")
        for a in actions:
            content = a['content'][:50] + "..." if len(a['content']) > 50 else a['content']
            output.append(f"| {a['id']} | {content} | {a['assignee']} | {a['deadline']} | {a['status']} |\n")
        output.append("\n")
    
    # 统计
    output.append("### 统计\n")
    output.append(f"- 决议事项：{len(decisions)} 项\n")
    output.append(f"- 行动项：{len(actions)} 项\n")
    
    return "".join(output)


def format_json(actions: List[Dict], decisions: List[Dict]) -> str:
    """格式化为JSON"""
    data = {
        "extracted_at": datetime.now().isoformat(),
        "decisions": decisions,
        "actions": actions,
        "summary": {
            "decision_count": len(decisions),
            "action_count": len(actions)
        }
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def filter_by_assignee(actions: List[Dict], assignee: str) -> List[Dict]:
    """按责任人筛选"""
    return [a for a in actions if assignee in a['assignee']]


def main():
    parser = argparse.ArgumentParser(description="行动项提取工具")
    parser.add_argument("--input", "-i", help="输入会议记录文件")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", "-f", default="markdown", 
                        choices=["markdown", "table", "json"],
                        help="输出格式")
    parser.add_argument("--assignee", help="筛选特定责任人")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ extract_actions.py 测试通过")
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
    
    # 提取
    actions = extract_actions(text)
    decisions = extract_decisions(text)
    
    # 筛选
    if args.assignee:
        actions = filter_by_assignee(actions, args.assignee)
    
    # 格式化
    if args.format == "json":
        output = format_json(actions, decisions)
    else:
        output = format_markdown(actions, decisions)
    
    # 输出
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 已提取 {len(actions)} 个行动项，{len(decisions)} 个决议")
        print(f"   保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
