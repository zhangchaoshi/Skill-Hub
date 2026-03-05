#!/usr/bin/env python3
"""
Odoo PO Parallel Translator

为超大 PO 文件生成并行翻译脚本。此脚本会根据系统 CPU 核心数
自动调整并发数量，生成可在多个 Claude Code 会话中独立运行的翻译脚本。

使用方法：
1. 生成并行翻译脚本: python parallel_translator.py generate --chunk-dir ./chunks --script-dir ./scripts --output-dir ./translated --original-file large.pot
2. 合并翻译结果: python parallel_translator.py merge --original-file large.pot --chunks-dir ./translated --output zh_CN.po
"""

import argparse
import json
import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict
import multiprocessing


class ParallelTranslator:
    """生成和管理并行翻译脚本"""

    @staticmethod
    def detect_cpu_cores() -> int:
        """检测 CPU 核心数"""
        return multiprocessing.cpu_count()

    @staticmethod
    def get_chunk_files(chunk_dir: str) -> List[Path]:
        """获取所有 chunk 文件"""
        chunk_dir = Path(chunk_dir)
        if not chunk_dir.exists():
            raise FileNotFoundError(f"Chunk 目录不存在: {chunk_dir}")

        chunk_files = sorted(chunk_dir.glob('chunk_*.json'))
        if not chunk_files:
            raise FileNotFoundError(f"在 {chunk_dir} 中未找到 chunk 文件")

        return chunk_files

    @staticmethod
    def generate_translation_script(
        chunk_file: Path,
        script_dir: Path,
        output_dir: Path,
        max_retries: int = 3
    ) -> str:
        """
        为单个 chunk 生成翻译脚本

        Args:
            chunk_file: chunk 文件路径
            script_dir: 脚本输出目录
            output_dir: 翻译结果输出目录
            max_retries: 最大重试次数

        Returns:
            生成的脚本文件路径
        """
        script_name = f"translate_{chunk_file.stem}.sh"
        script_path = script_dir / script_name

        output_file = output_dir / f"{chunk_file.stem}_translated.json"
        prompt_file = output_dir / f"{chunk_file.stem}_prompt.txt"

        script_content = f"""#!/bin/bash
# Odoo PO Chunk 翻译脚本
# Chunk: {chunk_file.name}
# 生成时间: {__import__('datetime').datetime.now().isoformat()}

CHUNK_FILE="{chunk_file.absolute()}"
OUTPUT_FILE="{output_file.absolute()}"
PROMPT_FILE="{prompt_file.absolute()}"
MAX_RETRIES={max_retries}

echo "=========================================="
echo "开始翻译: {chunk_file.name}"
echo "=========================================="

# 重试逻辑
for i in $(seq 1 $MAX_RETRIES); do
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 尝试翻译 (第 $i/$MAX_RETRIES 次)"

    # 步骤 1: 生成翻译提示
    echo "生成翻译提示..."
    python {Path(__file__).parent / 'translate_chunk.py'} prompt "$CHUNK_FILE" --output "$PROMPT_FILE"

    if [ $? -ne 0 ]; then
        echo "错误: 生成翻译提示失败"
        if [ $i -lt $MAX_RETRIES ]; then
            echo "等待 5 秒后重试..."
            sleep 5
            continue
        else
            echo "错误: 达到最大重试次数，放弃此 chunk"
            exit 1
        fi
    fi

    # 步骤 2: 读取翻译提示并翻译
    # 注意: 这里需要人工或自动翻译 $PROMPT_FILE 中的内容
    # 翻译完成后，使用以下命令保存结果:
    #
    # python scripts/translate_chunk.py save "$CHUNK_FILE" "$OUTPUT_FILE" \\
    #   --translations "原文1: 译文1; 原文2: 译文2"
    #
    # 或者直接编辑 JSON 文件，填充 msgstr 字段

    # 步骤 3: 验证翻译结果
    if [ -f "$OUTPUT_FILE" ]; then
        echo "验证翻译结果..."
        python {Path(__file__).parent / 'translate_chunk.py'} validate "$OUTPUT_FILE"

        if [ $? -eq 0 ]; then
            echo ""
            echo "=========================================="
            echo "✓ 翻译完成: {chunk_file.name}"
            echo "=========================================="
            exit 0
        else
            echo "警告: 验证未通过"
            if [ $i -lt $MAX_RETRIES ]; then
                echo "等待 5 秒后重试..."
                sleep 5
                continue
            fi
        fi
    else
        echo "警告: 未找到翻译结果文件 $OUTPUT_FILE"
        if [ $i -lt $MAX_RETRIES ]; then
            echo "等待 5 秒后重试..."
            sleep 5
            continue
        fi
    fi

    echo "错误: 达到最大重试次数"
    exit 1
done
"""

        script_path.write_text(script_content, encoding='utf-8')
        script_path.chmod(0o755)

        return str(script_path)

    @staticmethod
    def generate_parallel_run_script(
        script_dir: Path,
        chunk_dir: Path,
        output_dir: Path,
        original_file: Path,
        max_workers: int = None
    ) -> str:
        """
        生成并行执行脚本

        Args:
            script_dir: 脚本目录
            chunk_dir: chunk 目录
            output_dir: 输出目录
            original_file: 原始 PO 文件
            max_workers: 最大并发数（None 表示使用 CPU 核心数）

        Returns:
            生成的并行执行脚本路径
        """
        script_path = script_dir / 'parallel_run.sh'

        if max_workers is None:
            workers = ParallelTranslator.detect_cpu_cores()
        else:
            workers = max_workers

        chunk_files = sorted(chunk_dir.glob('chunk_*.json'))
        chunk_count = len(chunk_files)

        script_content = f"""#!/bin/bash
# Odoo PO 并行翻译执行脚本
# 生成时间: {__import__('datetime').datetime.now().isoformat()}

SCRIPT_DIR="{script_dir.absolute()}"
CHUNK_DIR="{chunk_dir.absolute()}"
OUTPUT_DIR="{output_dir.absolute()}"
ORIGINAL_FILE="{original_file.absolute()}"
WORKERS={workers}

echo "=========================================="
echo "Odoo PO 并行翻译"
echo "=========================================="
echo "原始文件: {original_file.name}"
echo "Chunk 数量: {chunk_count}"
echo "并发任务数: $WORKERS"
echo "=========================================="
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 统计 chunk 文件数量
CHUNK_COUNT=$(find "$CHUNK_DIR" -name "chunk_*.json" | wc -l)
echo "找到 $CHUNK_COUNT 个 chunk 文件"
echo ""

# 并行执行所有翻译脚本
echo "开始并行翻译..."
echo ""

find "$SCRIPT_DIR" -name "translate_chunk_*.sh" | \\
    xargs -P "$WORKERS" -I {{}} bash {{}}

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ 所有翻译任务已完成"
else
    echo "⚠ 部分翻译任务失败"
    echo "退出码: $EXIT_CODE"
fi
echo "=========================================="
echo ""

# 统计翻译结果
TRANSLATED_COUNT=$(find "$OUTPUT_DIR" -name "*_translated.json" 2>/dev/null | wc -l)
echo "翻译结果: $TRANSLATED_COUNT / $CHUNK_COUNT"

if [ $TRANSLATED_COUNT -ne $CHUNK_COUNT ]; then
    echo ""
    echo "⚠ 警告: 部分 chunk 翻译失败"
    echo "失败的 chunk:"

    for chunk in "$CHUNK_DIR"/chunk_*.json; do
        chunk_name=$(basename "$chunk" .json)
        if [ ! -f "$OUTPUT_DIR/${{chunk_name}}_translated.json" ]; then
            echo "  - $chunk_name"
        fi
    done

    echo ""
    echo "您可以手动运行失败的翻译脚本:"
    echo "bash $SCRIPT_DIR/translate_chunk_<name>.sh"
    echo ""
else
    echo "✓ 所有 chunk 翻译完成"
fi

echo ""
echo "=========================================="
echo "开始合并翻译结果..."
echo "=========================================="

# 合并翻译结果
python {Path(__file__).parent / 'po_splitter.py'} merge "$ORIGINAL_FILE" \\
    --chunks-dir "$OUTPUT_DIR" \\
    --output "{original_file.parent / 'zh_CN.po'}"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 翻译完成！"
    echo "输出文件: {original_file.parent / 'zh_CN.po'}"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "⚠ 合并失败，请检查翻译结果"
    echo "=========================================="
    exit 1
fi
"""

        script_path.write_text(script_content, encoding='utf-8')
        script_path.chmod(0o755)

        return str(script_path)

    @staticmethod
    def generate_monitor_script(
        chunk_dir: Path,
        output_dir: Path
    ) -> str:
        """
        生成进度监控脚本

        Args:
            chunk_dir: chunk 目录
            output_dir: 输出目录

        Returns:
            生成的监控脚本路径
        """
        script_path = Path(__file__).parent / 'monitor_progress.sh'

        script_content = f"""#!/bin/bash
# Odoo PO 翻译进度监控脚本
# 使用方法: 在另一个终端中运行此脚本

CHUNK_DIR="{chunk_dir.absolute()}"
OUTPUT_DIR="{output_dir.absolute()}"

while true; do
    # 清屏
    clear 2>/dev/null || printf '\\033[2J\\033[H'

    echo "=========================================="
    echo "Odoo PO 翻译进度监控"
    echo "=========================================="
    echo ""

    # 统计 chunk 文件数量
    TOTAL=$(find "$CHUNK_DIR" -name "chunk_*.json" 2>/dev/null | wc -l)
    DONE=$(find "$OUTPUT_DIR" -name "*_translated.json" 2>/dev/null | wc -l)

    if [ $TOTAL -eq 0 ]; then
        echo "未找到 chunk 文件"
        exit 1
    fi

    PERCENT=$((DONE * 100 / TOTAL))

    echo "总数量: $TOTAL"
    echo "已完成: $DONE"
    echo "进度: $PERCENT%"
    echo ""

    # 进度条
    BAR_WIDTH=50
    FILLED=$((BAR_WIDTH * DONE / TOTAL))
    EMPTY=$((BAR_WIDTH - FILLED))

    printf "["
    for ((i=0; i<FILLED; i++)); do printf "="; done
    for ((i=0; i<EMPTY; i++)); do printf " "; done
    printf "]"
    echo ""

    # 显示未完成的 chunk
    if [ $DONE -lt $TOTAL ]; then
        echo ""
        echo "待翻译的 chunk:"

        for chunk in "$CHUNK_DIR"/chunk_*.json; do
            chunk_name=$(basename "$chunk" .json)
            if [ ! -f "$OUTPUT_DIR/${{chunk_name}}_translated.json" ]; then
                echo "  - $chunk_name"
            fi
        done | head -n 10

        if [ $((TOTAL - DONE)) -gt 10 ]; then
            echo "  ... 还有 $((TOTAL - DONE - 10)) 个"
        fi

        echo ""
        echo "按 Ctrl+C 退出监控"
    else
        echo ""
        echo "✓ 所有翻译任务已完成！"
        break
    fi

    sleep 2
done

echo ""
echo "监控结束"
"""

        script_path.write_text(script_content, encoding='utf-8')
        script_path.chmod(0o755)

        return str(script_path)

    @staticmethod
    def generate_summary(
        original_file: Path,
        chunk_files: List[Path],
        workers: int,
        max_retries: int
    ) -> str:
        """
        生成翻译摘要

        Args:
            original_file: 原始 PO 文件
            chunk_files: chunk 文件列表
            workers: 并发任务数
            max_retries: 最大重试次数

        Returns:
            摘要文本
        """
        file_size = original_file.stat().st_size / 1024 / 1024

        # 读取第一个 chunk 获取条目信息
        if chunk_files:
            with open(chunk_files[0], 'r', encoding='utf-8') as f:
                entries = json.load(f)
            entries_per_chunk = len(entries)
            total_entries = entries_per_chunk * len(chunk_files)
        else:
            entries_per_chunk = 0
            total_entries = 0

        summary = f"""
## 并行翻译摘要

**原文件**: {original_file.name}
**输出文件**: zh_CN.po
**文件大小**: {file_size:.2f} MB
**模式**: 并行分块翻译

### 文件统计
- 总条目数: {total_entries}
- 块文件数: {len(chunk_files)}
- 每块条目: {entries_per_chunk}

### 并行配置
- CPU 核心数: {ParallelTranslator.detect_cpu_cores()}
- 并发任务数: {workers}
- 最大重试次数: {max_retries}

### 性能估算
- 预计总耗时: ~{len(chunk_files) / workers:.1f}x 单块时间
- 平均每块并发: {workers}

### 使用说明
1. 在多个 Claude Code 会话中分别运行翻译脚本
2. 或使用一键并行执行: bash temp/scripts/parallel_run.sh
3. 在另一个终端监控进度: bash skills/odoo-po-translator/scripts/monitor_progress.sh
4. 所有翻译完成后自动合并为 zh_CN.po

注意: 翻译脚本会生成翻译提示文件，需要手动或使用翻译 API 进行翻译。
"""

        return summary

    @staticmethod
    def generate(
        chunk_dir: str,
        script_dir: str,
        output_dir: str,
        original_file: str,
        max_workers: int = None,
        max_retries: int = 3
    ) -> Dict:
        """
        生成所有并行翻译脚本

        Args:
            chunk_dir: chunk 文件目录
            script_dir: 脚本输出目录
            output_dir: 翻译结果输出目录
            original_file: 原始 PO 文件路径
            max_workers: 最大并发数（None 表示使用 CPU 核心数）
            max_retries: 最大重试次数

        Returns:
            生成结果统计
        """
        # 转换为 Path 对象
        chunk_dir = Path(chunk_dir)
        script_dir = Path(script_dir)
        output_dir = Path(output_dir)
        original_file = Path(original_file)

        # 创建目录
        script_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 检查原始文件
        if not original_file.exists():
            raise FileNotFoundError(f"原始 PO 文件不存在: {original_file}")

        # 获取 chunk 文件
        chunk_files = ParallelTranslator.get_chunk_files(str(chunk_dir))

        # 检测 CPU 核心数
        cpu_cores = ParallelTranslator.detect_cpu_cores()
        if max_workers is None:
            workers = cpu_cores
        else:
            workers = min(max_workers, cpu_cores)

        print(f"检测到 {cpu_cores} 个 CPU 核心")
        print(f"使用 {workers} 个并发任务")
        print(f"最大重试次数: {max_retries}")
        print()

        # 生成每个 chunk 的翻译脚本
        print("生成翻译脚本...")
        for chunk_file in chunk_files:
            script_path = ParallelTranslator.generate_translation_script(
                chunk_file, script_dir, output_dir, max_retries
            )
            print(f"  ✓ {script_path}")

        # 生成并行执行脚本
        print()
        print("生成并行执行脚本...")
        parallel_script = ParallelTranslator.generate_parallel_run_script(
            script_dir, chunk_dir, output_dir, original_file, workers
        )
        print(f"  ✓ {parallel_script}")

        # 生成监控脚本
        print()
        print("生成进度监控脚本...")
        monitor_script = ParallelTranslator.generate_monitor_script(
            chunk_dir, output_dir
        )
        print(f"  ✓ {monitor_script}")

        # 生成摘要
        print()
        summary = ParallelTranslator.generate_summary(
            original_file, chunk_files, workers, max_retries
        )

        print(summary)

        return {
            'total_chunks': len(chunk_files),
            'workers': workers,
            'max_retries': max_retries,
            'script_dir': str(script_dir),
            'parallel_script': parallel_script,
            'monitor_script': monitor_script
        }


def main():
    parser = argparse.ArgumentParser(
        description='Odoo PO Parallel Translator - 生成并行翻译脚本'
    )
    parser.add_argument('command', choices=['generate', 'merge'],
                       help='命令: generate(生成翻译脚本), merge(合并翻译结果)')
    parser.add_argument('--chunk-dir', help='chunk 文件目录')
    parser.add_argument('--script-dir', help='脚本输出目录')
    parser.add_argument('--output-dir', help='翻译结果输出目录')
    parser.add_argument('--original-file', help='原始 PO 文件路径')
    parser.add_argument('--max-workers', type=int,
                       help='最大并发任务数（默认: CPU 核心数）')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='最大重试次数（默认: 3）')

    args = parser.parse_args()

    if args.command == 'generate':
        if not args.chunk_dir or not args.script_dir or not args.output_dir or not args.original_file:
            parser.error(
                "generate 命令需要 --chunk-dir, --script-dir, --output-dir 和 --original-file 参数"
            )

        result = ParallelTranslator.generate(
            args.chunk_dir,
            args.script_dir,
            args.output_dir,
            args.original_file,
            args.max_workers,
            args.max_retries
        )

        print()
        print("✓ 所有脚本生成完成！")
        print()
        print("下一步操作:")
        print(f"  1. 并行执行: bash {result['parallel_script']}")
        print(f"  2. 监控进度: bash {result['monitor_script']}")

    elif args.command == 'merge':
        if not args.original_file or not args.chunk_dir:
            parser.error("merge 命令需要 --original-file 和 --chunk-dir 参数")

        output = args.output_dir or args.original_file.parent / 'zh_CN.po'

        # 导入 po_splitter 模块
        sys.path.insert(0, str(Path(__file__).parent))
        import po_splitter

        po_splitter.merge_files(
            args.original_file,
            args.chunk_dir,
            str(output)
        )

        print(f"✓ 合并完成！输出文件: {output}")


if __name__ == '__main__':
    main()
