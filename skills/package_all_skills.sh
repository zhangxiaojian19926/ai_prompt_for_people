#!/bin/bash
# package_all_skills.sh - 自动打包所有技能到 dist 目录
# 用法: ./package_all_skills.sh [输出目录]
# 默认输出到 skills/dist/

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR"

# 输出目录（支持命令行参数）
DIST_DIR="${1:-$SKILLS_DIR/dist}"

# 排除的目录（非技能目录）
EXCLUDE_DIRS="dist|--output-dir|scripts|assets|__pycache__|\.git"

# 创建输出目录
mkdir -p "$DIST_DIR"

echo "==========================================
🎁 技能打包工具 v2.0
==========================================
打包时间: $(date '+%Y-%m-%d %H:%M:%S')
技能目录: $SKILLS_DIR
输出目录: $DIST_DIR
"

# 统计变量
total_count=0
success_count=0
fail_count=0

# 自动发现所有技能目录
for skill_path in "$SKILLS_DIR"/*/; do
    # 获取目录名
    skill=$(basename "$skill_path")
    
    # 跳过排除的目录
    if echo "$skill" | grep -qE "^($EXCLUDE_DIRS)$"; then
        continue
    fi
    
    # 检查是否有 SKILL.md 文件（判断是否为有效技能）
    if [ ! -f "$skill_path/SKILL.md" ]; then
        continue
    fi
    
    ((total_count++))
    output_file="$DIST_DIR/${skill}.skill"
    
    echo "────────────────────────────────────────"
    echo "📦 打包: $skill"
    
    # 获取版本号
    version=$(grep -E "^version:" "$skill_path/SKILL.md" | head -1 | sed 's/version: *//')
    if [ -z "$version" ]; then
        version="未知"
    fi
    echo "   版本: $version"
    
    # 统计文件数量
    file_count=$(find "$skill_path" -type f | wc -l | tr -d ' ')
    echo "   文件数: $file_count"
    
    # 统计参考文档数量
    if [ -d "$skill_path/references" ]; then
        ref_count=$(find "$skill_path/references" -name "*.md" | wc -l | tr -d ' ')
        echo "   参考文档: $ref_count"
    fi
    
    # 创建 tar.gz 包（重命名为 .skill）
    cd "$SKILLS_DIR"
    if tar -czf "$output_file" "$skill" 2>/dev/null; then
        # 获取包大小
        size=$(ls -lh "$output_file" | awk '{print $5}')
        echo "   包大小: $size"
        echo "   ✅ 完成: $(basename $output_file)"
        ((success_count++))
    else
        echo "   ❌ 打包失败"
        ((fail_count++))
    fi
done

echo "
==========================================
📊 打包汇总
==========================================

发现技能: $total_count 个
成功打包: $success_count 个
打包失败: $fail_count 个

────────────────────────────────────────
📁 输出文件列表
────────────────────────────────────────"

# 显示所有打包文件
if [ -d "$DIST_DIR" ] && [ "$(ls -A $DIST_DIR/*.skill 2>/dev/null)" ]; then
    printf "%-40s %8s %10s\n" "文件名" "大小" "修改时间"
    echo "────────────────────────────────────────"
    for f in "$DIST_DIR"/*.skill; do
        fname=$(basename "$f")
        fsize=$(ls -lh "$f" | awk '{print $5}')
        ftime=$(stat -f "%Sm" -t "%m-%d %H:%M" "$f" 2>/dev/null || stat -c "%y" "$f" 2>/dev/null | cut -d' ' -f1)
        printf "%-40s %8s %10s\n" "$fname" "$fsize" "$ftime"
    done
fi

echo "
==========================================
✅ 打包完成！
==========================================

使用方式：
  1. 复制到目标目录: cp $DIST_DIR/*.skill ~/.claude/skills/
  2. 解压查看内容: tar -xzf xxx.skill
"
