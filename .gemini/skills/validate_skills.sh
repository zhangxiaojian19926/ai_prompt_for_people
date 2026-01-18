#!/bin/bash
# 技能质量验收脚本
# 用于验证所有技能是否达到生产级标准

SKILLS_DIR="${1:-./skills}"
PASS=0
WARN=0
FAIL=0

echo "=========================================="
echo "🔍 技能质量验收报告"
echo "=========================================="
echo "验收时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "验收目录: $SKILLS_DIR"
echo ""

for skill_dir in "$SKILLS_DIR"/*/; do
    if [ ! -d "$skill_dir" ]; then
        continue
    fi
    
    skill_name=$(basename "$skill_dir")
    echo "────────────────────────────────────────"
    echo "📦 技能: $skill_name"
    echo "────────────────────────────────────────"
    
    skill_pass=true
    skill_warnings=""
    
    # 1. 检查 SKILL.md 存在
    if [ ! -f "$skill_dir/SKILL.md" ]; then
        echo "  ❌ SKILL.md 不存在"
        skill_pass=false
        continue
    fi
    
    # 2. 检查 SKILL.md 行数 (≥70行)
    lines=$(wc -l < "$skill_dir/SKILL.md" | tr -d ' ')
    if [ "$lines" -ge 70 ]; then
        echo "  ✅ SKILL.md 行数: $lines (≥70)"
    else
        echo "  ⚠️  SKILL.md 行数: $lines (<70)"
        skill_warnings="$skill_warnings\n    - SKILL.md行数不足70行"
    fi
    
    # 3. 检查版本号
    if grep -q "^version:" "$skill_dir/SKILL.md"; then
        version=$(grep "^version:" "$skill_dir/SKILL.md" | head -1 | sed 's/version: *//')
        echo "  ✅ 版本号: $version"
    else
        echo "  ❌ 缺少版本号"
        skill_pass=false
    fi
    
    # 4. 检查功能矩阵
    if grep -q "功能.*触发关键词.*参考文档" "$skill_dir/SKILL.md"; then
        echo "  ✅ 包含功能矩阵表"
    else
        echo "  ⚠️  缺少功能矩阵表"
        skill_warnings="$skill_warnings\n    - 缺少功能矩阵表"
    fi
    
    # 5. 检查质量检查清单
    if grep -q "质量检查清单" "$skill_dir/SKILL.md"; then
        echo "  ✅ 包含质量检查清单"
    else
        echo "  ⚠️  缺少质量检查清单"
        skill_warnings="$skill_warnings\n    - 缺少质量检查清单"
    fi
    
    # 6. 检查常见陷阱
    if grep -q "常见陷阱" "$skill_dir/SKILL.md"; then
        echo "  ✅ 包含常见陷阱"
    else
        echo "  ⚠️  缺少常见陷阱"
        skill_warnings="$skill_warnings\n    - 缺少常见陷阱"
    fi
    
    # 7. 检查 references 目录
    ref_dir="$skill_dir/references"
    if [ -d "$ref_dir" ]; then
        ref_count=$(find "$ref_dir" -name "*.md" -type f | wc -l | tr -d ' ')
        if [ "$ref_count" -ge 6 ]; then
            echo "  ✅ 参考文档数量: $ref_count (≥6)"
        else
            echo "  ⚠️  参考文档数量: $ref_count (<6)"
            skill_warnings="$skill_warnings\n    - 参考文档数量不足6个"
        fi
        
        # 检查每个文档大小
        small_docs=""
        for doc in "$ref_dir"/*.md; do
            if [ -f "$doc" ]; then
                size=$(wc -c < "$doc" | tr -d ' ')
                if [ "$size" -lt 2500 ]; then
                    small_docs="$small_docs $(basename "$doc")"
                fi
            fi
        done
        if [ -z "$small_docs" ]; then
            echo "  ✅ 所有参考文档 ≥ 2.5KB"
        else
            echo "  ⚠️  文档 < 2.5KB:$small_docs"
            skill_warnings="$skill_warnings\n    - 以下文档小于2.5KB:$small_docs"
        fi
        
        # 计算总大小
        total_size=$(cat "$ref_dir"/*.md 2>/dev/null | wc -c | tr -d ' ')
        total_kb=$((total_size / 1024))
        if [ "$total_size" -ge 20000 ]; then
            echo "  ✅ 参考文档总大小: ${total_kb}KB (≥20KB)"
        else
            echo "  ⚠️  参考文档总大小: ${total_kb}KB (<20KB)"
            skill_warnings="$skill_warnings\n    - 参考文档总大小不足20KB"
        fi
    else
        echo "  ❌ references 目录不存在"
        skill_pass=false
    fi
    
    # 8. 检查占位符 (排除描述如何避免占位符的内容)
    placeholder_count=$(grep -rE "^[^#-]*[[:space:]]*(TODO|待补充|待完善|TBD)[[:space:]]*$" "$skill_dir" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$placeholder_count" -gt 0 ]; then
        echo "  ⚠️  发现真正的占位符($placeholder_count处)"
        skill_warnings="$skill_warnings\\n    - 存在占位符文字"
    else
        echo "  ✅ 无占位符"
    fi
    
    # 统计结果
    if [ "$skill_pass" = false ]; then
        echo ""
        echo "  🔴 状态: 未通过"
        ((FAIL++))
    elif [ -n "$skill_warnings" ]; then
        echo ""
        echo "  🟡 状态: 有待改进"
        echo -e "  改进项:$skill_warnings"
        ((WARN++))
    else
        echo ""
        echo "  🟢 状态: 生产级"
        ((PASS++))
    fi
    echo ""
done

# 总结
echo "=========================================="
echo "📊 验收总结"
echo "=========================================="
echo ""

total=$((PASS + WARN + FAIL))
echo "总计技能: $total"
echo "  🟢 生产级: $PASS"
echo "  🟡 待改进: $WARN"
echo "  🔴 未通过: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
    echo "✅ 所有技能均已达到生产级标准！"
elif [ "$FAIL" -eq 0 ]; then
    echo "⚠️  部分技能需要改进，但无严重问题。"
else
    echo "❌ 存在未通过的技能，需要修复。"
fi

echo ""
echo "=========================================="
