#!/usr/bin/env python3
"""
Odoo PO File Splitter

用于处理超大 PO 文件的工具。当 PO 文件超过 Claude 读取限制时，
使用此脚本将文件分割成可处理的小块。

使用方法：
1. 分割文件: python po_splitter.py split input.pot --chunks-dir ./chunks
2. 合并文件: python po_splitter.py merge input.pot ./chunks output.po
3. 统计信息: python po_splitter.py info input.pot
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class POSplitter:
    """PO 文件分割器，支持超大文件处理"""

    # PO 文件头部结束标记（第一个 msgid 前）
    HEADER_END_PATTERN = re.compile(r'^msgid ""$', re.MULTILINE)

    # 翻译条目开始标记
    ENTRY_START_PATTERN = re.compile(r'^#\.(module|odoo-python)', re.MULTILINE)

    # msgid/msgstr 提取模式
    MSGID_PATTERN = re.compile(r'^msgid\s+"(.+)"$', re.MULTILINE)
    MSGSTR_PATTERN = re.compile(r'^msgstr\s+"(.+)"$', re.MULTILINE)
    MSGID_PLURAL_PATTERN = re.compile(r'^msgid_plural\s+"(.+)"$', re.MULTILINE)
    MSGSTR_N_PATTERN = re.compile(r'^msgstr\[(\d+)\]\s+"(.+)"$', re.MULTILINE)

    # 条目边界模式（以注释行或空行开头的新条目）
    ENTRY_BOUNDARY_PATTERN = re.compile(r'\n(#\.(module|odoo-python)|#:\s*\w+)', re.MULTILINE)

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.encoding = 'utf-8'
        self.line_ending = '\n'

    def read_file_chunks(self, chunk_size: int = 8192) -> str:
        """流式读取文件内容，支持超大文件"""
        content = []
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                content.append(chunk)
        return ''.join(content)

    def get_file_size_mb(self) -> float:
        """获取文件大小（MB）"""
        return self.file_path.stat().st_size / (1024 * 1024)

    def parse_po_entries(self, content: str) -> List[Dict]:
        """
        解析 PO 文件，提取所有翻译条目

        返回格式:
        [
            {
                'header': '#. module: account\n#: model:ir.model.fields...',
                'msgid': 'Original text',
                'msgstr': 'Translated text',
                'is_plural': False,
                'plural_forms': {...},  # 如果是复数形式
                'is_empty': True,       # msgstr 是否为空
                'line_number': 100,     # 在原文件中的行号
                'original_block': '...'  # 原始块内容
            },
            ...
        ]
        """
        entries = []
        lines = content.split('\n')
        i = 0
        line_number = 0

        # 跳过头部（直到第一个 msgid）
        header_lines = []
        while i < len(lines):
            line = lines[i]
            header_lines.append(line)
            if line.startswith('msgid '):
                # 头部结束，回退
                header_lines.pop()
                break
            i += 1

        # 解析翻译条目
        while i < len(lines):
            entry = self._parse_entry(lines, i, line_number)
            if entry:
                entries.append(entry)
                i += entry['block_lines']  # 跳过已处理的行
                line_number += entry['block_lines']
            else:
                i += 1
                line_number += 1

        return entries, '\n'.join(header_lines)

    def _parse_entry(self, lines: List[str], start_idx: int, line_number: int) -> Dict:
        """解析单个翻译条目"""
        entry = {
            'header': '',
            'msgid': '',
            'msgstr': '',
            'is_plural': False,
            'plural_forms': {},
            'is_empty': True,
            'line_number': line_number,
            'block_lines': 0,
            'original_block': ''
        }

        if start_idx >= len(lines):
            return None

        # 收集注释行（header）
        header_lines = []
        i = start_idx
        while i < len(lines) and (lines[i].startswith('#') or lines[i].strip() == ''):
            header_lines.append(lines[i])
            i += 1

        if not header_lines:
            return None  # 不是有效的条目开始

        entry['header'] = '\n'.join(header_lines)

        # 查找 msgid
        msgid_lines = []
        msgstr_lines = []
        msgid_plural_lines = []
        msgstr_n_lines = {}  # {0: [...], 1: [...]}

        # 解析 msgid
        if i < len(lines) and lines[i].startswith('msgid '):
            msgid_line = lines[i]
            msgid_match = re.match(r'^msgid\s+"(.*)"$', msgid_line)
            if msgid_match:
                entry['msgid'] = msgid_match.group(1)
                # 处理多行字符串
                j = i + 1
                while j < len(lines) and lines[j].startswith('"'):
                    entry['msgid'] += lines[j].strip('"')
                    j += 1
                i = j

        # 检查是否有复数形式
        if i < len(lines) and lines[i].startswith('msgid_plural '):
            entry['is_plural'] = True
            msgid_plural_match = re.match(r'^msgid_plural\s+"(.*)"$', lines[i])
            if msgid_plural_match:
                entry['plural_forms']['msgid_plural'] = msgid_plural_match.group(1)
                # 处理多行
                j = i + 1
                while j < len(lines) and lines[j].startswith('"'):
                    entry['plural_forms']['msgid_plural'] += lines[j].strip('"')
                    j += 1
                i = j

        # 解析 msgstr 或 msgstr[]
        if entry['is_plural']:
            # 复数形式：msgstr[0], msgstr[1], ...
            n = 0
            while i < len(lines) and lines[i].startswith(f'msgstr[{n}]'):
                msgstr_n_match = re.match(rf'^msgstr\[{n}\]\s+"(.*)"$', lines[i])
                if msgstr_n_match:
                    entry['plural_forms'][f'msgstr[{n}]'] = msgstr_n_match.group(1)
                    # 处理多行
                    j = i + 1
                    while j < len(lines) and lines[j].startswith('"'):
                        entry['plural_forms'][f'msgstr[{n}]'] += lines[j].strip('"')
                        j += 1
                    i = j
                    n += 1
                else:
                    i += 1
        else:
            # 单数形式：msgstr
            if i < len(lines) and lines[i].startswith('msgstr '):
                msgstr_match = re.match(r'^msgstr\s+"(.*)"$', lines[i])
                if msgstr_match:
                    entry['msgstr'] = msgstr_match.group(1)
                    # 处理多行
                    j = i + 1
                    while j < len(lines) and lines[j].startswith('"'):
                        entry['msgstr'] += lines[j].strip('"')
                        j += 1
                    i = j

        # 检查是否为空翻译
        entry['is_empty'] = (not entry['is_plural'] and entry['msgstr'] == '') or \
                             (entry['is_plural'] and
                              all(v == '' for k, v in entry['plural_forms'].items()
                                  if k.startswith('msgstr')))

        # 重建原始块
        entry['original_block'] = entry['header']
        if entry['is_plural']:
            entry['original_block'] += f'msgid "{entry["msgid"]}"\n'
            if 'msgid_plural' in entry['plural_forms']:
                entry['original_block'] += f'msgid_plural "{entry["plural_forms"]["msgid_plural"]}"\n'
            n = 0
            while f'msgstr[{n}]' in entry['plural_forms']:
                entry['original_block'] += f'msgstr[{n}] "{entry["plural_forms"][f"msgstr[{n}]"]}"\n'
                n += 1
        else:
            entry['original_block'] += f'msgid "{entry["msgid"]}"\n'
            entry['original_block'] += f'msgstr "{entry["msgstr"]}"\n'

        entry['block_lines'] = i - start_idx
        return entry

    def split_by_entries(self, entries: List[Dict], entries_per_chunk: int = 50,
                         chunk_dir: str = './chunks') -> List[str]:
        """
        按条目数量分割文件

        Args:
            entries: 解析后的条目列表
            entries_per_chunk: 每个块的条目数量
            chunk_dir: 输出目录

        Returns:
            生成的块文件路径列表
        """
        chunk_dir = Path(chunk_dir)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_files = []
        total_chunks = (len(entries) + entries_per_chunk - 1) // entries_per_chunk

        for chunk_idx in range(total_chunks):
            start = chunk_idx * entries_per_chunk
            end = min(start + entries_per_chunk, len(entries))
            chunk_entries = entries[start:end]

            chunk_file = chunk_dir / f'chunk_{chunk_idx:04d}.json'
            with open(chunk_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_entries, f, ensure_ascii=False, indent=2)

            chunk_files.append(str(chunk_file))

        return chunk_files

    def generate_po_from_entries(self, header: str, entries: List[Dict]) -> str:
        """从条目列表生成 PO 文件内容"""
        content = header + '\n'

        for entry in entries:
            content += '\n' + entry['original_block']

        return content

    def merge_chunks(self, chunk_dir: str, header: str, output_path: str) -> str:
        """
        合并翻译后的块文件

        Args:
            chunk_dir: 块文件目录
            header: PO 文件头部
            output_path: 输出文件路径

        Returns:
            合并后的 PO 内容
        """
        chunk_dir = Path(chunk_dir)

        # 读取所有块文件，按顺序排序
        chunk_files = sorted(chunk_dir.glob('chunk_*.json'),
                            key=lambda x: int(x.stem.split('_')[1]))

        all_entries = []
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
                all_entries.extend(entries)

        content = self.generate_po_from_entries(header, all_entries)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content

    def get_statistics(self, entries: List[Dict]) -> Dict:
        """获取翻译条目统计信息"""
        stats = {
            'total_entries': len(entries),
            'empty_entries': sum(1 for e in entries if e['is_empty']),
            'translated_entries': sum(1 for e in entries if not e['is_empty']),
            'plural_entries': sum(1 for e in entries if e['is_plural']),
            'single_entries': sum(1 for e in entries if not e['is_plural']),
        }
        stats['completion_rate'] = (
            stats['translated_entries'] / stats['total_entries'] * 100
            if stats['total_entries'] > 0 else 0
        )
        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Odoo PO File Splitter - 处理超大 PO 文件'
    )
    parser.add_argument('command', choices=['split', 'merge', 'info'],
                       help='命令: split(分割), merge(合并), info(统计)')
    parser.add_argument('input_file', help='输入 PO/POT 文件路径')

    # split 命令参数
    parser.add_argument('--chunks-dir', default='./chunks',
                       help='分割块输出目录 (默认: ./chunks)')
    parser.add_argument('--entries-per-chunk', type=int, default=50,
                       help='每个块的条目数量 (默认: 50)')

    # merge 命令参数
    parser.add_argument('--output', '-o', help='合并后的输出文件路径')

    args = parser.parse_args()

    splitter = POSplitter(args.input_file)
    file_size_mb = splitter.get_file_size_mb()

    print(f"文件: {args.input_file}")
    print(f"大小: {file_size_mb:.2f} MB")

    if args.command == 'info':
        content = splitter.read_file_chunks()
        entries, header = splitter.parse_po_entries(content)
        stats = splitter.get_statistics(entries)
        print("\n=== 统计信息 ===")
        print(f"总条目数: {stats['total_entries']}")
        print(f"空条目数: {stats['empty_entries']}")
        print(f"已翻译条目: {stats['translated_entries']}")
        print(f"完成率: {stats['completion_rate']:.1f}%")
        print(f"复数形式条目: {stats['plural_entries']}")

    elif args.command == 'split':
        content = splitter.read_file_chunks()
        entries, header = splitter.parse_po_entries(content)

        # 保存头部到单独文件
        header_file = Path(args.chunks_dir) / 'header.txt'
        Path(args.chunks_dir).mkdir(parents=True, exist_ok=True)
        with open(header_file, 'w', encoding='utf-8') as f:
            f.write(header)

        # 分割条目
        chunk_files = splitter.split_by_entries(
            entries, args.entries_per_chunk, args.chunks_dir
        )

        print(f"\n=== 分割完成 ===")
        print(f"头部文件: {header_file}")
        print(f"块文件数: {len(chunk_files)}")
        print(f"输出目录: {args.chunks_dir}")
        print(f"\n建议使用 entries_per_chunk={args.entries_per_chunk}")
        print(f"每个块约 {args.entries_per_chunk} 个条目")

    elif args.command == 'merge':
        if not args.output:
            parser.error("--output 参数在 merge 命令中是必须的")

        header_file = Path(args.chunks_dir) / 'header.txt'
        if not header_file.exists():
            print(f"错误: 找不到头部文件 {header_file}")
            return

        with open(header_file, 'r', encoding='utf-8') as f:
            header = f.read()

        splitter.merge_chunks(args.chunks_dir, header, args.output)
        print(f"\n=== 合并完成 ===")
        print(f"输出文件: {args.output}")


if __name__ == '__main__':
    main()
