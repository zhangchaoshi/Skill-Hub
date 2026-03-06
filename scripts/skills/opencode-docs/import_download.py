#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _rel_to_source_url(rel_path: Path) -> str | None:
    rel = rel_path.as_posix()
    if not rel.endswith(".md"):
        return None

    if rel == "index.md":
        return "https://opencode.ai/docs/zh-cn"

    if rel.endswith("/index.md"):
        rel_dir = rel[: -len("/index.md")]
        return f"https://opencode.ai/docs/zh-cn/{rel_dir}"

    # best-effort fallback
    rel_no_ext = re.sub(r"\.md$", "", rel)
    return f"https://opencode.ai/docs/zh-cn/{rel_no_ext}"


def _ensure_source_header(dst_path: Path, url: str) -> None:
    if dst_path.suffix.lower() != ".md":
        return

    text = dst_path.read_text(encoding="utf-8")
    header = f"<!-- source: {url} -->\n\n"
    if text.startswith("<!-- source: "):
        return
    dst_path.write_text(header + text, encoding="utf-8")


def import_download(src_root: Path, dst_root: Path) -> None:
    if not src_root.exists() or not src_root.is_dir():
        raise SystemExit(f"Source does not exist or is not a directory: {src_root}")

    _ensure_dir(dst_root)

    copied = 0
    skipped = 0
    ignored = 0
    for src_path in src_root.rglob("*"):
        if src_path.is_dir():
            continue

        if src_path.suffix.lower() != ".md":
            ignored += 1
            continue

        rel = src_path.relative_to(src_root)
        dst_path = dst_root / rel
        _ensure_dir(dst_path.parent)

        url = _rel_to_source_url(rel)

        if dst_path.exists():
            # Only overwrite if source is newer or sizes differ
            src_stat = src_path.stat()
            dst_stat = dst_path.stat()
            if src_stat.st_mtime <= dst_stat.st_mtime and src_stat.st_size == dst_stat.st_size:
                if url is not None:
                    _ensure_source_header(dst_path, url)
                skipped += 1
                continue

        shutil.copy2(src_path, dst_path)
        if url is not None:
            _ensure_source_header(dst_path, url)
        copied += 1

    print(f"Imported from: {src_root}")
    print(f"Imported to:   {dst_root}")
    print(f"Files copied:  {copied}")
    print(f"Files skipped: {skipped}")
    print(f"Files ignored: {ignored}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Firecrawl download output into repo-tracked references, preserving structure."
    )
    parser.add_argument("--from", dest="src", required=True, help="Source directory (e.g. .firecrawl/.../docs/zh-cn)")
    parser.add_argument(
        "--to",
        dest="dst",
        required=True,
        help="Destination directory (e.g. skills/opencode-docs/references/opencode.ai/docs/zh-cn)",
    )
    args = parser.parse_args()

    src_root = Path(os.path.expanduser(args.src)).resolve()
    dst_root = Path(os.path.expanduser(args.dst)).resolve()
    import_download(src_root, dst_root)


if __name__ == "__main__":
    main()
