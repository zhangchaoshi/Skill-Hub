#!/usr/bin/env python3
"""
Odoo PO Chunk Translator

翻译单个 chunk 文件中的空条目。此脚本用于配合 po_splitter.py
处理超大 PO 文件的分块翻译。

使用方法：
1. 生成翻译提示: python translate_chunk.py prompt chunk_0000.json --output prompt.txt
2. 保存翻译结果: python translate_chunk.py save chunk_0000.json translated.json --translations "原文1: 译文1; 原文2: 译文2"
3. 验证翻译结果: python translate_chunk.py validate translated.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set
import re


class ChunkTranslator:
    """处理单个 PO 翻译块"""

    # 占位符模式
    PLACEHOLDER_PATTERNS = [
        r'%[sdf]',           # %s, %d, %f
        r'%\([a-z_]+\)[sdf]',  # %(name)s, %(count)d
        r'\{[^}]+\}',        # {name}
        r'<[^>]+>',          # HTML tags
        r'&[a-z]+;',         # HTML entities like &lt;, &gt;, &amp;
    ]

    @staticmethod
    def extract_placeholders(text: str) -> Set[str]:
        """提取文本中的占位符"""
        placeholders = set()
        for pattern in ChunkTranslator.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, text)
            placeholders.update(matches)
        return placeholders

    @staticmethod
    def validate_entry(entry: Dict, translations: Dict[str, str]) -> Dict:
        """
        验证翻译条目

        Args:
            entry: 条目对象
            translations: 翻译字典 {msgid: msgstr}

        Returns:
            验证结果，包含错误列表
        """
        result = {
            'entry_line': entry.get('line_number', 'unknown'),
            'msgid': entry['msgid'],
            'errors': [],
            'warnings': []
        }

        msgid = entry['msgid']
        if msgid not in translations:
            result['errors'].append('缺少翻译')
            return result

        msgstr = translations[msgid]

        # 检查占位符是否保留
        msgid_placeholders = ChunkTranslator.extract_placeholders(msgid)
        msgstr_placeholders = ChunkTranslator.extract_placeholders(msgstr)

        missing = msgid_placeholders - msgstr_placeholders
        if missing:
            result['errors'].append(f'缺失占位符: {", ".join(missing)}')

        extra = msgstr_placeholders - msgid_placeholders
        if extra:
            result['warnings'].append(f'多余占位符: {", ".join(extra)}')

        # 检查翻译是否为空
        if not msgstr.strip():
            result['errors'].append('翻译为空')

        return result

    @staticmethod
    def generate_translation_prompt(chunk_file: str, max_entries: int = 10) -> str:
        """
        为翻译块生成提示文本

        Args:
            chunk_file: chunk JSON 文件路径
            max_entries: 最多显示的条目数量

        Returns:
            翻译提示文本
        """
        with open(chunk_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)

        empty_entries = [e for e in entries if e['is_empty']]

        prompt = f"""# Odoo PO 文件翻译任务

此块包含 {len(entries)} 个条目，其中 {len(empty_entries)} 个需要翻译。

## 待翻译条目（显示前 {min(max_entries, len(empty_entries))} 个）：

"""

        for i, entry in enumerate(empty_entries[:max_entries]):
            context = entry.get('header', '').strip()
            context_preview = context[:100] + '...' if len(context) > 100 else context

            prompt += f"""
### 条目 {i+1}

**上下文**:
```
{context_preview}
```

**原文 (msgid)**:
```
{entry['msgid']}
```

"""

            if entry.get('is_plural') and 'msgid_plural' in entry.get('plural_forms', {}):
                prompt += f"""**复数形式**:
```
{entry['plural_forms']['msgid_plural']}
```

"""

            # 显示占位符
            placeholders = ChunkTranslator.extract_placeholders(entry['msgid'])
            if placeholders:
                prompt += f"**占位符**: {', '.join(placeholders)}\n"

            prompt += "\n"

        if len(empty_entries) > max_entries:
            prompt += f"\n*（还有 {len(empty_entries) - max_entries} 个条目未显示）*\n"

        prompt += """
## 翻译要求

1. **保持占位符**: 确保所有占位符（如 %s, %(name)d, HTML 标签等）在翻译中完全保留
2. **复数形式**: 复数条目需要翻译 msgid 和 msgid_plural
3. **术语一致性**: 使用 Odoo 标准术语翻译
4. **输出格式**: 请按以下 JSON 格式返回翻译结果：

```json
{
  "原文1": "译文1",
  "原文2": "译文2",
  ...
}
```

## 常见 Odoo 术语参考

| 英文 | 中文 |
|------|------|
| partner | 合作伙伴/业务伙伴 |
| product | 产品 |
| sale/sales | 销售 |
| purchase | 采购 |
| invoice | 发票 |
| move | 凭证/移动 |
| journal | 日记账 |
| company | 公司 |
| user | 用户 |
| account | 账户/科目 |
| tax | 税 |
| warehouse | 仓库 |
| order | 订单 |
| quote/quotation | 报价单 |
| customer | 客户 |
| vendor/supplier | 供应商 |
| employee | 员工 |
| draft | 草稿 |
| confirmed | 已确认 |
| done/closed | 已完成/已关闭 |
| cancelled | 已取消 |

请开始翻译：
"""
        return prompt

    @staticmethod
    def save_translations(chunk_file: str, output_file: str,
                         translations: Dict[str, str]) -> Dict:
        """
        将翻译结果保存到 chunk 文件

        Args:
            chunk_file: 原始 chunk 文件
            output_file: 输出文件
            translations: 翻译字典 {msgid: msgstr}

        Returns:
            保存结果统计
        """
        with open(chunk_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)

        translated_count = 0
        skipped_count = 0

        for entry in entries:
            if entry['is_empty'] and entry['msgid'] in translations:
                if entry.get('is_plural'):
                    # 复数形式，msgstr 需要单独处理
                    # 这里简化处理，实际需要更复杂的逻辑
                    entry['msgstr'] = translations[entry['msgid']]
                else:
                    entry['msgstr'] = translations[entry['msgid']]
                entry['is_empty'] = False
                translated_count += 1
            else:
                skipped_count += 1

        # 保存到输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        return {
            'total_entries': len(entries),
            'translated': translated_count,
            'skipped': skipped_count
        }

    @staticmethod
    def generate_batch_script(chunk_dir: str, output_dir: str) -> str:
        """
        生成批处理脚本，用于逐块翻译

        Args:
            chunk_dir: 块文件目录
            output_dir: 输出目录

        Returns:
            批处理脚本内容
        """
        chunk_dir = Path(chunk_dir)
        output_dir = Path(output_dir)

        chunk_files = sorted(chunk_dir.glob('chunk_*.json'))

        script = f"""#!/bin/bash
# Odoo PO 批翻译脚本
# 由 translate_chunk.py 生成

CHUNK_DIR="{chunk_dir}"
OUTPUT_DIR="{output_dir}"
mkdir -p "$OUTPUT_DIR"

echo "找到 {{len(chunk_files)}} 个块文件需要翻译"
echo ""

"""

        for i, chunk_file in enumerate(chunk_files):
            output_file = output_dir / f"{chunk_file.stem}_translated.json"
            prompt_file = output_dir / f"{chunk_file.stem}_prompt.txt"

            script += f"""
# === 块 {i+1}: {chunk_file.name} ===
echo "处理块 {i+1}/{len(chunk_files)}: {chunk_file.name}"

# 生成翻译提示
python scripts/translate_chunk.py prompt "{chunk_file}" --output "{prompt_file}"

# TODO: 手动翻译或使用翻译API处理提示文件，然后保存结果
# python scripts/translate_chunk.py save "{chunk_file}" "{output_file}" --translations "..."



"""

        script += """
echo ""
echo "所有翻译提示已生成。"
echo "请翻译每个 prompt.txt 文件，然后运行 save 命令保存结果。"
echo ""
echo "翻译完成后，使用 po_splitter.py 合并所有翻译后的块文件。"
"""
        return script


def main():
    parser = argparse.ArgumentParser(
        description='Odoo PO Chunk Translator - 翻译单个 PO 块'
    )
    parser.add_argument('command', choices=['prompt', 'save', 'validate', 'batch'],
                       help='命令: prompt(生成提示), save(保存翻译), validate(验证), batch(生成批处理)')
    parser.add_argument('chunk_file', help='chunk JSON 文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--translations', help='翻译结果，格式: "原文1: 译文1; 原文2: 译文2"')
    parser.add_argument('--max-entries', type=int, default=10,
                       help='prompt 命令显示的最大条目数')
    parser.add_argument('--chunk-dir', help='batch 命令的块文件目录')
    parser.add_argument('--output-dir', help='batch 命令的输出目录')

    args = parser.parse_args()

    if args.command == 'prompt':
        if not args.output:
            args.output = args.chunk_file.replace('.json', '_prompt.txt')

        prompt = ChunkTranslator.generate_translation_prompt(
            args.chunk_file, args.max_entries
        )

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"翻译提示已生成: {args.output}")
        print(f"文件大小: {len(prompt)} 字符")

    elif args.command == 'save':
        if not args.output:
            args.output = args.chunk_file.replace('.json', '_translated.json')

        if not args.translations:
            print("错误: --translations 参数是必须的")
            return

        # 解析翻译结果
        translations = {}
        for item in args.translations.split(';'):
            item = item.strip()
            if ':' in item:
                key, value = item.split(':', 1)
                translations[key.strip()] = value.strip()

        result = ChunkTranslator.save_translations(
            args.chunk_file, args.output, translations
        )

        print(f"翻译结果已保存: {args.output}")
        print(f"总条目: {result['total_entries']}")
        print(f"已翻译: {result['translated']}")
        print(f"跳过: {result['skipped']}")

    elif args.command == 'validate':
        with open(args.chunk_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)

        print(f"验证文件: {args.chunk_file}")
        print(f"总条目: {len(entries)}")
        print("")

        errors_found = False
        for entry in entries:
            if not entry['is_empty']:
                translations = {entry['msgid']: entry['msgstr']}
                result = ChunkTranslator.validate_entry(entry, translations)
                if result['errors']:
                    errors_found = True
                    print(f"行 {result['entry_line']}: {result['msgid'][:50]}...")
                    for error in result['errors']:
                        print(f"  错误: {error}")
                    if result['warnings']:
                        for warning in result['warnings']:
                            print(f"  警告: {warning}")
                    print("")

        if not errors_found:
            print("验证通过，未发现错误。")

    elif args.command == 'batch':
        if not args.chunk_dir or not args.output_dir:
            parser.error("--chunk-dir 和 --output-dir 参数在 batch 命令中是必须的")

        script = ChunkTranslator.generate_batch_script(
            args.chunk_dir, args.output_dir
        )

        script_file = Path(args.output_dir) / 'translate_chunks.sh'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script)

        print(f"批处理脚本已生成: {script_file}")
        print("请运行: bash " + str(script_file))


if __name__ == '__main__':
    main()
