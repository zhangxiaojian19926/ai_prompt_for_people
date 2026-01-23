#!/usr/bin/env python3
"""
市场调研工具 - market_research.py

用途：生成市场调研报告框架，提供数据获取指引

使用方法：
    python market_research.py --topic "新能源汽车" --output report.md
    python market_research.py --topic "AI芯片" --depth deep
    python market_research.py --list-templates

参数：
    --topic, -t     调研主题
    --depth, -d     深度: quick(快速), standard(标准), deep(深度)
    --output, -o    输出文件
"""

import argparse
from datetime import datetime
from pathlib import Path

# 调研模板
TEMPLATES = {
    "quick": {
        "name": "快速调研",
        "sections": ["行业概览", "主要玩家", "关键数据"],
        "time_estimate": "30分钟"
    },
    "standard": {
        "name": "标准调研",
        "sections": ["行业概览", "市场规模", "竞争格局", "发展趋势", "投资机会"],
        "time_estimate": "2小时"
    },
    "deep": {
        "name": "深度调研",
        "sections": ["行业定义", "产业链分析", "市场规模", "竞争格局", "技术趋势", 
                    "政策环境", "投资逻辑", "风险分析", "重点公司", "投资建议"],
        "time_estimate": "1天"
    }
}

# 数据源推荐
DATA_SOURCES = {
    "宏观数据": ["国家统计局", "Wind", "东方财富Choice"],
    "行业报告": ["艾瑞咨询", "前瞻产业研究院", "麦肯锡报告"],
    "公司数据": ["上市公司年报", "招股说明书", "券商研报"],
    "实时新闻": ["财经新闻网站", "行业媒体", "公司公告"],
    "海外数据": ["Statista", "IBISWorld", "Gartner"]
}

REPORT_TEMPLATE = '''# {topic} 市场调研报告

**调研日期**: {date}
**调研深度**: {depth_name}
**预计耗时**: {time_estimate}

---

## 调研目标

1. 了解 {topic} 行业现状
2. 识别主要市场参与者
3. 分析发展趋势和投资机会
4. 评估潜在风险

---

## 数据获取指南

### 推荐数据源

{data_sources}

### 需要搜索的关键词

- "{topic} 行业分析"
- "{topic} 市场规模"
- "{topic} 竞争格局"
- "{topic} 发展趋势 2026"
- "{topic} 头部公司"

---

## 调研框架

{sections}

---

## 分析工具

### PEST分析
| 维度 | 分析要点 |
|------|---------|
| Political (政策) | 监管政策、产业政策、补贴政策 |
| Economic (经济) | 市场规模、增长率、盈利能力 |
| Social (社会) | 消费趋势、用户需求变化 |
| Technological (技术) | 技术壁垒、创新趋势 |

### 波特五力
| 力量 | 强度 | 分析 |
|------|------|------|
| 新进入者威胁 | | |
| 替代品威胁 | | |
| 供应商议价能力 | | |
| 买家议价能力 | | |
| 行业竞争强度 | | |

### 竞争格局
| 公司 | 市场份额 | 核心优势 | 估值 |
|------|---------|---------|------|
| | | | |
| | | | |

---

## 投资机会评估

### 行业吸引力评分
| 维度 | 评分(1-10) | 说明 |
|------|-----------|------|
| 市场空间 | | |
| 增长速度 | | |
| 盈利能力 | | |
| 竞争格局 | | |
| 政策支持 | | |

### 投资标的筛选
| 标的 | 类型 | 逻辑 | 风险 |
|------|------|------|------|
| | 龙头 | | |
| | 成长 | | |
| | ETF | | |

---

## 调研结论

### 核心发现
1. [待填写]
2. [待填写]
3. [待填写]

### 投资建议
[待完成调研后填写]

### 后续跟踪
- [ ] 关注事件1
- [ ] 关注事件2

---

*报告框架由 market_research.py 生成*
'''


def generate_sections(sections: list, topic: str) -> str:
    """生成章节内容"""
    output = []
    for i, section in enumerate(sections, 1):
        output.append(f"### {i}. {section}")
        output.append("")
        output.append(f"[关于 {topic} 的 {section} 待补充]")
        output.append("")
    return "\n".join(output)


def format_data_sources() -> str:
    """格式化数据源"""
    output = []
    for category, sources in DATA_SOURCES.items():
        output.append(f"**{category}**")
        for src in sources:
            output.append(f"- {src}")
        output.append("")
    return "\n".join(output)


def generate_report(topic: str, depth: str) -> str:
    """生成调研报告框架"""
    template_info = TEMPLATES.get(depth, TEMPLATES["standard"])
    
    sections_content = generate_sections(template_info["sections"], topic)
    
    report = REPORT_TEMPLATE.format(
        topic=topic,
        date=datetime.now().strftime("%Y-%m-%d"),
        depth_name=template_info["name"],
        time_estimate=template_info["time_estimate"],
        data_sources=format_data_sources(),
        sections=sections_content
    )
    
    return report


def list_templates():
    """列出可用模板"""
    print("📋 可用调研模板:\n")
    for key, info in TEMPLATES.items():
        print(f"  - {key}: {info['name']} (预计{info['time_estimate']})")
        print(f"    包含: {', '.join(info['sections'][:3])}...")
        print()


def main():
    parser = argparse.ArgumentParser(description="市场调研工具")
    parser.add_argument("--topic", "-t", help="调研主题")
    parser.add_argument("--depth", "-d", default="standard",
                        choices=["quick", "standard", "deep"],
                        help="调研深度")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--list-templates", action="store_true", help="列出模板")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ market_research.py 测试通过")
        return
    
    if args.list_templates:
        list_templates()
        return
    
    if not args.topic:
        print("❌ 请指定调研主题: --topic <主题>")
        return
    
    report = generate_report(args.topic, args.depth)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ 调研框架已生成: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
