# 智能翻译参考文档

## 概述

智能翻译功能用于多语言文档处理，支持术语表管理和双语对照输出。

## 支持语言

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| `zh` | 中文 | `en` | English |
| `ja` | 日本語 | `ko` | 한국어 |
| `fr` | Français | `de` | Deutsch |
| `es` | Español | `auto` | 自动检测 |

## 翻译策略

### 1. 语义翻译
- 理解原文含义
- 用目标语言自然表达
- 保持文化适配

### 2. 术语处理
- 专业术语保持一致性
- 支持自定义术语表
- 首次出现标注原文

### 3. 格式保持
- 保留 Markdown 格式
- 保持段落结构
- 保留代码块不翻译

## 术语表格式

```json
{
  "Machine Learning": "机器学习",
  "Deep Learning": "深度学习",
  "Neural Network": "神经网络",
  "API": "API（接口）"
}
```

## 输出格式

### 标准输出
```markdown
## 翻译文档

### 元信息
- 原语言：English
- 目标语言：中文
- 专业领域：技术文档

### 译文
[翻译后的内容]

### 术语对照表
| 原文 | 译文 | 备注 |
|------|------|------|
| API | 接口 | 技术术语 |
```

### 双语对照
```markdown
| 原文 | 译文 |
|------|------|
| Hello World | 你好世界 |
| This is a test. | 这是一个测试。 |
```

## Python 脚本使用

```bash
# 基本翻译（英译中）
python scripts/translate.py -i doc.md -t zh

# 指定源语言
python scripts/translate.py -i doc.md -s en -t zh

# 使用术语表
python scripts/translate.py -i doc.md -t zh -g glossary.json

# 双语对照输出
python scripts/translate.py -i doc.md -t zh --bilingual -o result.md
```

## 质量标准

- ✅ 术语翻译准确一致
- ✅ 语句通顺自然
- ✅ 保持原文格式
- ✅ 提供术语对照表
