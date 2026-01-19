# 数据表格处理参考文档

## 概述

表格处理功能用于CSV/Excel数据转换为Markdown表格，支持数据清洗和格式化。

## 支持格式

| 输入格式 | 扩展名 | 说明 |
|---------|--------|------|
| CSV | `.csv` | 逗号分隔值 |
| Excel | `.xlsx`, `.xls` | 需要 openpyxl 库 |

## 处理能力

### 数据清洗
- 移除空行
- 去除重复行
- 标准化空格

### 格式转换
- 自动检测表头
- 列数对齐
- 对齐方式可选

### 数据限制
- 默认最大100行
- 可通过参数调整
- 超限自动截断

## 输出格式

```markdown
## 数据表格

### 数据概览
- 数据来源：`data.csv`
- 行数：50 条数据
- 列数：5

### 数据表
| 姓名 | 部门 | 职位 | 入职日期 | 状态 |
|------|------|------|---------|------|
| 张三 | 研发部 | 工程师 | 2023-01-15 | 在职 |
| 李四 | 产品部 | 产品经理 | 2022-06-20 | 在职 |

### 数据说明
- 姓名：员工姓名
- 部门：所属部门
- ...
```

## 对齐方式

| 参数 | 效果 | Markdown |
|------|------|----------|
| `left` | 左对齐 | `\|---\|` |
| `center` | 居中 | `\|:---:\|` |
| `right` | 右对齐 | `\|---:\|` |

## Python 脚本使用

```bash
# CSV 转 Markdown
python scripts/table_converter.py -i data.csv -o table.md

# Excel 转换（指定工作表）
python scripts/table_converter.py -i data.xlsx --sheet "Sheet1"

# 数据清洗
python scripts/table_converter.py -i data.csv --clean

# 居中对齐
python scripts/table_converter.py -i data.csv --align center

# 限制行数
python scripts/table_converter.py -i data.csv --max-rows 50
```

## 依赖安装

```bash
# Excel 支持
pip install openpyxl
```

## 质量标准

- ✅ 表格结构完整
- ✅ 数据无丢失
- ✅ 列对齐正确
- ✅ 提供数据概览
