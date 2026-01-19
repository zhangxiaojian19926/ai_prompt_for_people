#!/usr/bin/env python3
"""
提示词评估工具 - evaluate_prompt.py

用途：评估提示词质量，生成评估报告

使用方法：
    python evaluate_prompt.py --input prompt.md --output report.md
    python evaluate_prompt.py --input prompt.md --verbose
    python evaluate_prompt.py --input prompt.md --criteria custom_criteria.json

参数：
    --input, -i     提示词文件路径
    --output, -o    评估报告输出路径
    --criteria      自定义评估标准JSON
    --verbose       详细输出
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 评估维度和权重
EVALUATION_CRITERIA = {
    "structure": {
        "name": "结构完整性",
        "weight": 0.2,
        "checks": [
            ("has_role", "是否有角色定义", ["# Role", "## 角色", "角色定义", "你是"]),
            ("has_task", "是否有任务说明", ["## 任务", "Task", "目标", "请你", "你需要"]),
            ("has_output", "是否有输出格式", ["## 输出", "Output", "格式", "返回"]),
            ("has_example", "是否有示例", ["## 示例", "Example", "例如", "比如"]),
        ]
    },
    "clarity": {
        "name": "表达清晰度",
        "weight": 0.2,
        "checks": [
            ("no_vague_words", "避免模糊词汇", None),  # 特殊检查
            ("has_specific_instructions", "有具体指令", ["必须", "需要", "应该", "请"]),
            ("has_constraints", "有约束条件", ["禁止", "不要", "避免", "限制"]),
        ]
    },
    "completeness": {
        "name": "内容完整度",
        "weight": 0.2,
        "checks": [
            ("word_count", "字数充足", None),  # 特殊检查
            ("has_context", "有上下文说明", ["背景", "场景", "Context", "Background"]),
            ("has_error_handling", "有异常处理", ["如果", "当", "错误", "失败", "异常"]),
        ]
    },
    "actionability": {
        "name": "可执行性",
        "weight": 0.2,
        "checks": [
            ("has_workflow", "有工作流程", ["步骤", "流程", "1.", "第一", "首先"]),
            ("has_decision_points", "有决策点", ["如果", "否则", "当", "选择"]),
            ("has_specific_actions", "有具体动作", ["分析", "生成", "提取", "创建", "输出"]),
        ]
    },
    "quality": {
        "name": "质量标准",
        "weight": 0.2,
        "checks": [
            ("has_quality_criteria", "有质量标准", ["质量", "标准", "检查", "验证"]),
            ("no_placeholders", "无占位符", None),  # 特殊检查
            ("proper_formatting", "格式规范", None),  # 特殊检查
        ]
    }
}

# 模糊词汇列表
VAGUE_WORDS = ["相关", "合适", "适当", "一些", "某些", "等等", "可能", "大概"]


def check_pattern(text: str, patterns: List[str]) -> bool:
    """检查文本是否包含任一模式"""
    text_lower = text.lower()
    for pattern in patterns:
        if pattern.lower() in text_lower:
            return True
    return False


def check_vague_words(text: str) -> Tuple[bool, List[str]]:
    """检查模糊词汇"""
    found = [word for word in VAGUE_WORDS if word in text]
    return len(found) == 0, found


def check_placeholders(text: str) -> Tuple[bool, List[str]]:
    """检查占位符"""
    placeholders = re.findall(r'\[.{0,20}?\]|\{.{0,20}?\}|TODO|TBD|待填写', text)
    # 过滤Markdown链接
    placeholders = [p for p in placeholders if not re.match(r'\[.+\]\(.+\)', p)]
    return len(placeholders) < 3, placeholders[:5]


def check_formatting(text: str) -> Tuple[bool, str]:
    """检查格式规范"""
    issues = []
    
    # 检查标题层级
    headers = re.findall(r'^#+', text, re.MULTILINE)
    if headers and not text.strip().startswith('#'):
        issues.append("非标题开头")
    
    # 检查空行
    if '\n\n\n' in text:
        issues.append("连续多个空行")
    
    return len(issues) == 0, ", ".join(issues) if issues else "格式良好"


def evaluate_dimension(text: str, dimension: dict) -> Tuple[float, List[dict]]:
    """评估单个维度"""
    results = []
    passed = 0
    total = len(dimension["checks"])
    
    for check_id, check_name, patterns in dimension["checks"]:
        if check_id == "no_vague_words":
            passed_check, details = check_vague_words(text)
            note = f"发现模糊词: {', '.join(details)}" if details else "无模糊词"
        elif check_id == "word_count":
            word_count = len(text)
            passed_check = word_count >= 200
            note = f"字数: {word_count}"
        elif check_id == "no_placeholders":
            passed_check, details = check_placeholders(text)
            note = f"占位符: {', '.join(details)}" if details else "无占位符"
        elif check_id == "proper_formatting":
            passed_check, note = check_formatting(text)
        else:
            passed_check = check_pattern(text, patterns)
            note = "✓" if passed_check else "未找到相关内容"
        
        results.append({
            "name": check_name,
            "passed": passed_check,
            "note": note
        })
        
        if passed_check:
            passed += 1
    
    score = passed / total if total > 0 else 0
    return score, results


def evaluate_prompt(text: str) -> dict:
    """评估提示词"""
    evaluation = {
        "timestamp": datetime.now().isoformat(),
        "word_count": len(text),
        "dimensions": {},
        "overall_score": 0,
        "grade": "",
        "summary": ""
    }
    
    total_weighted_score = 0
    
    for dim_id, dim_config in EVALUATION_CRITERIA.items():
        score, results = evaluate_dimension(text, dim_config)
        weighted_score = score * dim_config["weight"]
        total_weighted_score += weighted_score
        
        evaluation["dimensions"][dim_id] = {
            "name": dim_config["name"],
            "score": round(score * 100),
            "weight": dim_config["weight"],
            "checks": results
        }
    
    evaluation["overall_score"] = round(total_weighted_score * 100)
    
    # 评级
    if evaluation["overall_score"] >= 90:
        evaluation["grade"] = "A (优秀)"
    elif evaluation["overall_score"] >= 80:
        evaluation["grade"] = "B (良好)"
    elif evaluation["overall_score"] >= 70:
        evaluation["grade"] = "C (合格)"
    elif evaluation["overall_score"] >= 60:
        evaluation["grade"] = "D (待改进)"
    else:
        evaluation["grade"] = "E (不合格)"
    
    return evaluation


def format_report(evaluation: dict) -> str:
    """格式化评估报告"""
    output = ["# 提示词评估报告\n"]
    output.append(f"**评估时间**: {evaluation['timestamp'][:19]}")
    output.append(f"**字数**: {evaluation['word_count']}")
    output.append(f"**总体评分**: {evaluation['overall_score']}/100")
    output.append(f"**评级**: {evaluation['grade']}\n")
    
    output.append("## 维度评分\n")
    output.append("| 维度 | 得分 | 权重 |")
    output.append("|------|------|------|")
    
    for dim_id, dim_data in evaluation["dimensions"].items():
        output.append(f"| {dim_data['name']} | {dim_data['score']}% | {dim_data['weight']*100:.0f}% |")
    
    output.append("\n## 详细检查\n")
    
    for dim_id, dim_data in evaluation["dimensions"].items():
        output.append(f"### {dim_data['name']}\n")
        for check in dim_data["checks"]:
            status = "✅" if check["passed"] else "❌"
            output.append(f"- {status} {check['name']}: {check['note']}")
        output.append("")
    
    output.append("## 改进建议\n")
    for dim_id, dim_data in evaluation["dimensions"].items():
        failed_checks = [c for c in dim_data["checks"] if not c["passed"]]
        if failed_checks:
            output.append(f"### {dim_data['name']}")
            for check in failed_checks:
                output.append(f"- 建议添加: {check['name']}")
            output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="提示词评估工具")
    parser.add_argument("--input", "-i", help="提示词文件路径")
    parser.add_argument("--output", "-o", help="评估报告输出路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ evaluate_prompt.py 测试通过")
        return
    
    if not args.input:
        print("❌ 请指定提示词文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 评估
    evaluation = evaluate_prompt(text)
    
    # 生成报告
    report = format_report(evaluation)
    
    # 输出
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ 评估报告已保存到: {args.output}")
        print(f"   评分: {evaluation['overall_score']}/100 ({evaluation['grade']})")
    else:
        print(report)


if __name__ == "__main__":
    main()
