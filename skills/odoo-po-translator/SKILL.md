---
name: odoo-po-translator
description: 用于 Odoo .po 文件的简体中文汉化和翻译质量检查。自动翻译空条目、辅助翻译/校对、检测翻译质量问题。支持超大文件（>256KB）的分块处理。保持占位符格式、处理复数形式、维护术语一致性。当用户需要翻译 .po 文件、检查 po 文件质量、汉化 Odoo 模块、处理 Odoo 国际化文件、翻译 msgid 为 msgstr、或需要保持 Odoo 术语翻译一致性时使用此技能。
---

# Odoo .po 文件简体中文汉化

本技能用于处理 Odoo 框架的翻译文件（.po 格式），提供以下功能：

1. **自动翻译** - 将空的 msgstr 填充为简体中文翻译
2. **辅助翻译/校对** - 分析现有翻译并提供改进建议
3. **质量检查** - 检测翻译中的格式错误、占位符丢失等问题
4. **超大文件支持** - 通过分块脚本处理超过 256KB 的 PO 文件

## 使用时机

当用户请求以下任一任务时使用此技能：
- 翻译 Odoo .po 文件或 .pot 文件
- 检查 .po 文件的翻译质量
- 汉化 Odoo 模块
- 保持 Odoo 术语翻译一致性
- 修复 .po 文件中的翻译问题

## Odoo 翻译规范遵循

### PO 文件格式

```po
#. module: module_name
#: model_terms:ir.ui.view,arch_db:module_name.view_id
msgid "原文文本"
msgstr "翻译文本"
```

### 关键规范

**占位符处理** - 必须完全保留原始占位符：
- `%s`、`%d`、`%f` 等格式化占位符
- `%(name)s`、`%(count)d` 等命名占位符
- HTML 标签如 `<a>`、`<strong>`、`<br/>` 等
- 转义字符如 `&lt;`、`&gt;`、`&amp;` 等

**复数形式** - Odoo 使用 `msgid_plural` 和 `msgstr[]` 处理复数：
```po
msgid "One file"
msgid_plural "%(count)s files"
msgstr[0] "一个文件"
msgstr[1] "%(count)s 个文件"
```

**翻译块完整性** - 保持文本在单个块中，不要分割字符串。

## 工作流程

### 超大文件检测（新增）

在读取文件前，先检测文件大小：

```bash
# 检查文件大小
ls -lh file.pot
# 或
python -c "import os; print(f'{os.path.getsize(\"file.pot\")/1024/1024:.2f} MB')"
```

**如果文件超过 256KB（约 15000 行）**，必须使用脚本分块处理流程（见下方"超大文件处理流程"）。

**如果文件小于 256KB**，继续使用标准流程。

---

### 第一步：分析请求

识别用户的任务类型：
- 如果用户说"翻译"、"汉化"、"自动翻译" → 使用自动翻译模式
- 如果用户说"检查"、"校对"、"review" → 使用质量检查模式
- 如果用户说"改进"、"优化"或提及已有翻译 → 使用辅助翻译/校对模式

### 第二步：读取文件

使用 Read 工具读取目标 .po 文件。

### 第三步：分析翻译内容

提取以下信息：
1. 模块名称（从 `#.` 注释中获取）
2. 空翻译条目（msgstr 为空的条目）
3. 占位符列表（每个 msgid 中的占位符）
4. 复数形式条目
5. 模糊翻译标记（#, fuzzy）

### 第四步：根据模式处理

#### 模式 A：自动翻译空条目

1. 逐个处理空翻译条目
2. 翻译 msgid 为简体中文
3. 确保保留所有占位符和格式标记
4. 使用 Odoo 常见术语翻译（见下文术语表）
5. 保持模块内翻译一致性

#### 模式 B：辅助翻译/校对

1. 分析现有翻译质量
2. 识别可能的问题：
   - 占位符丢失或格式错误
   - 翻译不一致（相同原文有不同翻译）
   - 明显的机器翻译痕迹
   - 术语使用不当
3. 提供改进建议

#### 模式 C：质量检查

1. 检查每个条目的 msgstr 是否：
   - 包含 msgid 中的所有占位符
   - 正确处理复数形式
   - 保留 HTML 标签和转义字符
2. 列出发现的问题和位置
3. 提供修复建议

### 第五步：输出结果

**重要：不要修改原文件！**

创建新的 zh_CN.po 文件，包含：
- 原文件的所有内容（头信息、注释、msgid 等）
- 翻译后的 msgstr 内容

输出文件命名规则：
- 如果原文件是 `account.pot` → 创建 `zh_CN.po`
- 如果原文件是 `module_name.pot` → 创建 `zh_CN.po`
- 如果原文件是 `en_US.po` → 创建 `zh_CN.po`

新文件与原文件除 msgstr 内容外，所有其他内容完全相同。

## Odoo 常见术语翻译表

| 英文 | 中文 | 说明 |
|------|------|------|
| partner | 合作伙伴/业务伙伴 | 客户、供应商、合作伙伴的统称 |
| product | 产品 | 商品、物料 |
| sale/sales | 销售 | 销售、销售订单 |
| purchase | 采购 | 采购、采购订单 |
| invoice | 发票/单据 | 财务单据 |
| move | 凭证/移动 | 会计凭证、库存移动 |
| journal | 日记账/账本 | 会计日记账 |
| company | 公司 | 组织、公司 |
| user | 用户 | 系统用户 |
| account | 账户/科目 | 会计科目 |
| tax | 税 | 税收、税费 |
| warehouse | 仓库 | 仓储 |
| location | 库位 | 具体存储位置 |
| picking | 拣货/调拨 | 库存移动单据 |
| order | 订单 | 订单 |
| quote/s quotation | 报价单 | 销售报价 |
| receipt | 收据 | 收货单据 |
| delivery | 交付/发货 | 发货单据 |
| vendor/supplier | 供应商 | 供应商 |
| customer | 客户 | 客户 |
| employee | 员工 | 员工 |
| department | 部门 | 部门 |
| category | 分类/类别 | 分类 |
| tag | 标签 | 标签 |
| template | 模板 | 模板 |
| workflow | 工作流 | 业务流程 |
| state/status | 状态 | 状态 |
| draft | 草稿 | 草稿状态 |
| confirmed | 已确认 | 已确认状态 |
| done/closed | 已完成/已关闭 | 完成状态 |
| cancelled | 已取消 | 取消状态 |

## 术语一致性处理

当提供参考翻译文件时：
1. 读取参考文件
2. 提取术语对（原文 → 译文）
3. 在翻译新文件时优先使用已有术语翻译
4. 确保相同术语在不同文件中翻译一致

## 输出摘要格式

在创建新文件前，先输出摘要：

```
## 翻译摘要

**原文件**: [原文件名]
**输出文件**: zh_CN.po
**模块**: [模块名]
**模式**: [翻译模式]

### 变更统计
- 空条目总数: [数字]
- 已翻译: [数字]
- 跳过（已有翻译）: [数字]
- 发现问题: [数字]

### 主要问题
1. [问题描述] - 条目 #[行号]
2. ...

### 术语一致性
- 使用参考文件: [是/否]
- 术语匹配数: [数字]
```

## 常见问题处理

**占位符格式错误**：确保占位符与原文完全一致，包括类型和数量。

**HTML 标签错误**：检查标签是否成对闭合，转义是否正确。

**复数形式错误**：简体中文通常不需要复数变化，但需保持 msgstr[] 数组结构。

**过长翻译**：中文通常比英文短，但某些专业术语可能更长，注意布局问题。

**模糊翻译标记**：对于标记为 fuzzy 的条目，建议重新翻译确认。

## 注意事项

- **不要修改原文件**，始终使用 Write 工具创建新的 zh_CN.po 文件
- 创建前先输出摘要，让用户了解处理内容
- 新文件保持原文件的所有头信息、注释、msgid 等内容不变
- 对于不确定的翻译，保留原文或添加注释说明
- 上下文很重要，相同的英文在不同模块中可能有不同翻译
- 技术术语优先使用 Odoo 官方翻译

---

## 超大文件处理流程（>256KB）

当 PO 文件超过读取限制时，使用以下流程：

### 检测文件大小

```bash
# 检查文件大小
python -c "import os; size=os.path.getsize('1.pot'); print(f'{size/1024/1024:.2f} MB')"
```

### 分步处理流程

#### 步骤 1：分割文件

使用 `po_splitter.py` 将大文件分割成小块：

```bash
cd skills/odoo-po-translator/scripts
python po_splitter.py split ../../1.pot --chunks-dir ./temp/chunks --entries-per-chunk 30
```

参数说明：
- `--chunks-dir`: 块文件输出目录
- `--entries-per-chunk`: 每块包含的条目数，建议 20-50（根据每个条目大小调整）

输出文件：
- `temp/chunks/header.txt` - PO 文件头部信息
- `temp/chunks/chunk_0000.json` ~ `chunk_NNNN.json` - 翻译块（JSON 格式）

#### 步骤 2：统计文件信息

```bash
python po_splitter.py info ../../1.pot
```

查看总条目数、空条目数、完成率等统计信息。

#### 步骤 3：逐块翻译

对于每个 chunk 文件：

**方式 A：使用 translate_chunk.py 生成提示**

```bash
# 生成翻译提示（显示前 10 个空条目）
python translate_chunk.py prompt temp/chunks/chunk_0000.json --output temp/chunks/chunk_0000_prompt.txt

# 查看生成的提示
cat temp/chunks/chunk_0000_prompt.txt
```

**方式 B：直接读取 JSON 文件翻译**

```bash
# 读取 chunk 文件查看内容
cat temp/chunks/chunk_0000.json
```

对于每个块，读取其内容并翻译其中的 `is_empty: true` 条目。

翻译完成后，保存翻译结果：

```bash
python translate_chunk.py save temp/chunks/chunk_0000.json temp/chunks/chunk_0000_translated.json --translations "Original text 1: 翻译文本1; Original text 2: 翻译文本2"
```

**注意**：在实际使用中，更高效的方式是直接编辑 JSON 文件，将每个条目的 `msgstr` 字段填入翻译，并将 `is_empty` 改为 `false`。

#### 步骤 4：合并文件

所有块翻译完成后，使用 `po_splitter.py merge` 合并：

```bash
# 确保翻译后的 chunk 文件都在 chunks 目录中，文件名格式为 chunk_XXXX.json
python po_splitter.py merge ../../1.pot --chunks-dir ./temp/chunks --output zh_CN.po
```

### 批处理脚本

生成批处理脚本以便批量处理所有块：

```bash
python translate_chunk.py batch --chunk-dir ./temp/chunks --output-dir ./temp/batch_output
```

这将生成一个 `translate_chunks.sh` 脚本，包含所有块的翻译命令。

### JSON 块文件格式

每个 chunk JSON 文件包含一个数组，每个元素代表一个翻译条目：

```json
[
  {
    "header": "#. module: account\n#: model:ir.model.fields,field_description:account.field_account_journal__name",
    "msgid": "Journal Name",
    "msgstr": "",
    "is_plural": false,
    "plural_forms": {},
    "is_empty": true,
    "line_number": 100,
    "block_lines": 3,
    "original_block": "#. module: account\nmsgid \"Journal Name\"\nmsgstr \"\""
  }
]
```

翻译时，只需修改 `msgstr` 字段并将 `is_empty` 改为 `false`。

### 验证翻译结果

使用 `translate_chunk.py validate` 验证翻译后的 chunk 文件：

```bash
python translate_chunk.py validate temp/chunks/chunk_0000_translated.json
```

这会检查：
- 占位符是否完整
- 翻译是否为空
- 格式是否正确

### 完整示例

```bash
# 1. 进入脚本目录
cd skills/odoo-po-translator/scripts

# 2. 创建临时目录
mkdir -p temp/chunks

# 3. 分割文件（640KB 的 account.pot）
python po_splitter.py split ../../1.pot --chunks-dir ./temp/chunks --entries-per-chunk 30

# 4. 查看统计
python po_splitter.py info ../../1.pot

# 5. 逐块翻译（例如：翻译 chunk_0000.json）
# 先读取内容
cat temp/chunks/chunk_0000.json

# 翻译后编辑 JSON 文件，填充 msgstr 字段

# 6. 验证翻译
python translate_chunk.py validate temp/chunks/chunk_0000.json

# 7. 对所有块重复步骤 5-6

# 8. 合并结果
python po_splitter.py merge ../../1.pot --chunks-dir ./temp/chunks --output ../../zh_CN.po

# 9. 清理临时文件
rm -rf temp
```

### 超大文件输出摘要格式

使用超大文件流程时，输出以下摘要：

```
## 大文件翻译摘要

**原文件**: [原文件名]
**输出文件**: zh_CN.po
**文件大小**: [大小] MB
**模式**: 分块翻译

### 文件统计
- 总条目数: [数字]
- 空条目数: [数字]
- 已翻译: [数字]
- 块文件数: [数字]
- 每块条目: [数字]

### 处理进度
- 已处理块: [当前]/[总数]
- 已翻译条目: [数字]/[总数]

### 注意事项
- 使用分块处理流程，每块包含约 N 个条目
- 确保合并前所有块都已正确翻译
- 使用 validate 命令检查翻译质量
```
