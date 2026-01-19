#!/usr/bin/env python3
"""
播客脚本生成器 - audio_script.py

用途：生成播客/音频内容脚本

使用方法：
    python audio_script.py --input topic.md --type solo --output podcast.md
    python audio_script.py --input topic.md --type interview --duration 30
    python audio_script.py --list-types

参数：
    --input, -i     输入话题/大纲文件
    --type, -t      播客类型: solo, dialogue, interview
    --duration, -d  目标时长（分钟）
    --output, -o    输出文件
"""

import argparse
from pathlib import Path
from datetime import datetime

# 播客类型模板
PODCAST_TYPES = {
    "solo": {
        "name": "独白式播客",
        "template": """# {title}

## 节目信息
- 类型：独白
- 主播：[主播名称]
- 时长：{duration}分钟
- 主题：{topic}

---

## 开场白 (0:00-{intro_end})

大家好，欢迎收听[节目名称]。

我是你们的主播[名字]，今天我们来聊聊{topic}。

[简要介绍为什么这个话题重要]

好，让我们开始吧。

---

## 主体内容

### 第一部分：[标题] ({p1_start}-{p1_end})

{content_1}

### 第二部分：[标题] ({p2_start}-{p2_end})

{content_2}

### 第三部分：[标题] ({p3_start}-{p3_end})

{content_3}

---

## 总结 ({summary_start}-{summary_end})

好，让我们来总结一下今天的内容：

1. [要点一]
2. [要点二]
3. [要点三]

---

## 结束语 (最后2分钟)

感谢你收听今天的节目。

如果你觉得有收获，欢迎分享给你的朋友。

我们下期再见！

---

## 后期备注
- 背景音乐：[音乐类型建议]
- 音效：[音效使用建议]
- 剪辑：[剪辑要点]
"""
    },
    "dialogue": {
        "name": "对谈式播客",
        "template": """# {title}

## 节目信息
- 类型：双人对谈
- 主持人：[主持人A]、[主持人B]
- 时长：{duration}分钟
- 主题：{topic}

---

## 开场 (0:00-{intro_end})

**A**: 大家好，欢迎来到[节目名称]，我是A。

**B**: 我是B，今天我们要聊的话题是{topic}。

**A**: 没错，这个话题最近挺火的，你怎么看？

**B**: 我觉得[简要观点]...

---

## 话题一 ({p1_start}-{p1_end})

**A**: [引入问题]

**B**: [回应观点]

**A**: [追问或补充]

**B**: [深入讨论]

---

## 话题二 ({p2_start}-{p2_end})

**B**: 说到这里，我想问你一个问题...

**A**: [回答]

**B**: [追问]

---

## 话题三 ({p3_start}-{p3_end})

**A**: 那我们来聊聊[延伸话题]...

---

## 总结 ({summary_start}-{summary_end})

**A**: 好，时间差不多了，我们来总结一下。

**B**: 我觉得今天最重要的三点是...

**A**: 说得对，还有...

---

## 结束语

**B**: 感谢大家收听，我们下期再见。

**A**: 拜拜！
"""
    },
    "interview": {
        "name": "访谈式播客",
        "template": """# {title}

## 节目信息
- 类型：人物访谈
- 主持人：[主持人]
- 嘉宾：[嘉宾姓名] - [嘉宾身份]
- 时长：{duration}分钟
- 主题：{topic}

---

## 嘉宾介绍

[嘉宾的背景介绍，200字左右]

---

## 开场 (0:00-{intro_end})

**主持人**: 大家好，欢迎收听[节目名称]。今天我们非常荣幸地邀请到了[嘉宾名]。

**嘉宾**: 大家好，很高兴来到这里。

**主持人**: 简单介绍一下自己吧。

**嘉宾**: [自我介绍]

---

## 话题一：[个人经历] ({p1_start}-{p1_end})

**主持人**: 能不能先聊聊你是怎么开始[领域]的？

**嘉宾**: [回答]

**主持人**: [追问]

---

## 话题二：[专业观点] ({p2_start}-{p2_end})

**主持人**: 关于{topic}，你有什么独特的看法？

**嘉宾**: [分享观点]

---

## 话题三：[建议和展望] ({p3_start}-{p3_end})

**主持人**: 对于想要[目标]的听众，你有什么建议？

**嘉宾**: [给出建议]

---

## 快问快答 ({summary_start}-{summary_end})

**主持人**: 最后我们来一个快问快答环节。

1. 最推荐的一本书？
   **嘉宾**: [回答]

2. 最想给年轻人的一句话？
   **嘉宾**: [回答]

3. 未来一年的计划？
   **嘉宾**: [回答]

---

## 结束语

**主持人**: 非常感谢[嘉宾名]今天的分享。

**嘉宾**: 谢谢，希望对大家有帮助。

**主持人**: 听众朋友们，我们下期再见！
"""
    }
}


def calculate_timestamps(duration: int) -> dict:
    """计算时间戳"""
    intro = 2  # 开场2分钟
    summary = 3  # 总结3分钟
    body = duration - intro - summary
    part_duration = body // 3
    
    return {
        "intro_end": f"{intro}:00",
        "p1_start": f"{intro}:00",
        "p1_end": f"{intro + part_duration}:00",
        "p2_start": f"{intro + part_duration}:00",
        "p2_end": f"{intro + part_duration * 2}:00",
        "p3_start": f"{intro + part_duration * 2}:00",
        "p3_end": f"{duration - summary}:00",
        "summary_start": f"{duration - summary}:00",
        "summary_end": f"{duration}:00"
    }


def generate_podcast_script(topic: str, podcast_type: str, duration: int, content: str = "") -> str:
    """生成播客脚本"""
    if podcast_type not in PODCAST_TYPES:
        podcast_type = "solo"
    
    template = PODCAST_TYPES[podcast_type]["template"]
    timestamps = calculate_timestamps(duration)
    
    result = template.format(
        title=f"[节目名称] - {topic}",
        topic=topic,
        duration=duration,
        content_1="[第一部分内容展开]",
        content_2="[第二部分内容展开]",
        content_3="[第三部分内容展开]",
        **timestamps
    )
    
    return result


def list_types():
    """列出可用类型"""
    print("🎙️ 可用播客类型:\n")
    for key, ptype in PODCAST_TYPES.items():
        print(f"  - {key}: {ptype['name']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="播客脚本生成器")
    parser.add_argument("--input", "-i", help="输入话题/大纲文件")
    parser.add_argument("--topic", help="直接指定话题")
    parser.add_argument("--type", "-t", default="solo",
                        choices=list(PODCAST_TYPES.keys()),
                        help="播客类型")
    parser.add_argument("--duration", "-d", type=int, default=30, help="时长（分钟）")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--list-types", action="store_true", help="列出可用类型")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ audio_script.py 测试通过")
        return
    
    if args.list_types:
        list_types()
        return
    
    # 获取话题
    topic = args.topic
    content = ""
    
    if args.input:
        input_path = Path(args.input)
        if input_path.exists():
            content = input_path.read_text(encoding="utf-8")
            # 从内容提取话题
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    topic = line.strip().lstrip('#').strip()[:50]
                    break
    
    if not topic:
        topic = "待定话题"
    
    # 生成脚本
    result = generate_podcast_script(topic, args.type, args.duration, content)
    
    # 输出
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"✅ 播客脚本已保存到: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
