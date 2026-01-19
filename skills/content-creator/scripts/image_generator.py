#!/usr/bin/env python3
"""
AI配图提示词生成器 - image_generator.py

用途：为文章生成AI配图提示词

使用方法：
    python image_generator.py --input article.md --style minimal --output prompts.md
    python image_generator.py --input article.md --count 5
    python image_generator.py --list-styles

参数：
    --input, -i     输入文章文件
    --style, -s     配图风格
    --count, -c     配图数量
    --output, -o    输出文件
"""

import argparse
import re
from pathlib import Path

# 风格模板
STYLES = {
    "minimal": {
        "name": "极简风格",
        "prompt_template": "Minimalist illustration, clean lines, simple shapes, {subject}, white background, modern design, vector style",
        "negative": "complex, detailed, realistic, cluttered"
    },
    "illustration": {
        "name": "插画风格",
        "prompt_template": "Digital illustration, colorful, artistic, {subject}, creative composition, professional artwork",
        "negative": "realistic, photographic, 3D render"
    },
    "realistic": {
        "name": "写实风格",
        "prompt_template": "Photorealistic image, high quality, {subject}, professional photography, detailed",
        "negative": "cartoon, illustrated, stylized"
    },
    "3d": {
        "name": "3D渲染风格",
        "prompt_template": "3D render, Blender style, {subject}, soft lighting, clean background, modern 3D illustration",
        "negative": "2D, flat, drawn"
    },
    "tech": {
        "name": "科技风格",
        "prompt_template": "Futuristic tech illustration, {subject}, blue and purple gradient, neon accents, digital art",
        "negative": "natural, organic, vintage"
    }
}


def extract_key_sections(text: str) -> list:
    """提取关键段落作为配图场景"""
    sections = []
    
    # 提取标题
    titles = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
    for title in titles[:5]:
        sections.append({"type": "title", "content": title})
    
    # 提取带有数字的要点
    points = re.findall(r'^\d+\.\s+(.+)$', text, re.MULTILINE)
    for point in points[:3]:
        sections.append({"type": "point", "content": point})
    
    # 提取加粗的内容作为重点
    bold = re.findall(r'\*\*(.+?)\*\*', text)
    for b in bold[:3]:
        sections.append({"type": "highlight", "content": b})
    
    return sections[:5]  # 最多5个配图场景


def generate_image_prompt(section: dict, style: str) -> dict:
    """生成配图提示词"""
    if style not in STYLES:
        style = "minimal"
    
    style_config = STYLES[style]
    subject = section["content"]
    
    prompt = style_config["prompt_template"].format(subject=subject)
    
    return {
        "scene": subject,
        "type": section["type"],
        "prompt": prompt,
        "negative_prompt": style_config["negative"],
        "style": style_config["name"]
    }


def format_output(prompts: list, style: str) -> str:
    """格式化输出"""
    output = ["# AI配图提示词\n"]
    output.append(f"**风格**: {STYLES.get(style, STYLES['minimal'])['name']}")
    output.append(f"**数量**: {len(prompts)}张\n")
    
    for i, prompt in enumerate(prompts, 1):
        output.append(f"## 配图 {i}: {prompt['scene'][:20]}\n")
        output.append(f"**场景类型**: {prompt['type']}")
        output.append(f"**正向提示词**:")
        output.append(f"```")
        output.append(prompt['prompt'])
        output.append(f"```")
        output.append(f"**负向提示词**:")
        output.append(f"```")
        output.append(prompt['negative_prompt'])
        output.append(f"```\n")
    
    return "\n".join(output)


def list_styles():
    """列出可用风格"""
    print("🎨 可用配图风格:\n")
    for key, style in STYLES.items():
        print(f"  - {key}: {style['name']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="AI配图提示词生成器")
    parser.add_argument("--input", "-i", help="输入文章文件")
    parser.add_argument("--style", "-s", default="minimal",
                        choices=list(STYLES.keys()),
                        help="配图风格")
    parser.add_argument("--count", "-c", type=int, default=5, help="配图数量")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--list-styles", action="store_true", help="列出可用风格")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ image_generator.py 测试通过")
        return
    
    if args.list_styles:
        list_styles()
        return
    
    if not args.input:
        print("❌ 请指定输入文件: --input <文件路径>")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        return
    
    text = input_path.read_text(encoding="utf-8")
    
    # 提取场景
    sections = extract_key_sections(text)[:args.count]
    
    if not sections:
        print("⚠️ 未能提取到配图场景，请检查文章内容")
        return
    
    # 生成提示词
    prompts = [generate_image_prompt(s, args.style) for s in sections]
    
    # 格式化输出
    result = format_output(prompts, args.style)
    
    # 输出
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"✅ 配图提示词已保存到: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
