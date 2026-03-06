#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


SOURCE_RE = r"^<!--\s*source:\s*(https?://[^ ]+)\s*-->$"


def _extract_title(markdown_text: str) -> str | None:
    for line in markdown_text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return None


def _extract_source_url(markdown_text: str) -> str | None:
    import re

    for line in markdown_text.splitlines()[:10]:
        m = re.match(SOURCE_RE, line.strip())
        if m:
            return m.group(1)
    return None


def _iter_doc_markdown(doc_root: Path) -> list[Path]:
    md_files: list[Path] = []
    for p in sorted(doc_root.rglob("*.md")):
        rel = p.relative_to(doc_root).as_posix()
        if rel.startswith("assets/"):
            continue
        md_files.append(p)
    return md_files


def build_manifest(doc_root: Path, out_path: Path) -> None:
    if not doc_root.exists():
        raise SystemExit(f"Doc root does not exist: {doc_root}")

    entries: list[dict[str, str]] = []
    md_files = _iter_doc_markdown(doc_root)
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        title = _extract_title(text) or ""
        url = _extract_source_url(text) or ""

        local_path = md.relative_to(out_path.parent).as_posix()
        entries.append({"url": url, "local_path": local_path, "title": title})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Doc root:    {doc_root}")
    print(f"Manifest:    {out_path}")
    print(f"Entries:     {len(entries)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build manifest.json for the local opencode docs mirror.")
    parser.add_argument("--root", required=True, help="Mirror doc root (.../opencode.ai/docs/zh-cn)")
    parser.add_argument("--out", required=True, help="Output JSON path (e.g. skills/opencode-docs/references/manifest.json)")
    args = parser.parse_args()

    doc_root = Path(os.path.expanduser(args.root)).resolve()
    out_path = Path(os.path.expanduser(args.out)).resolve()
    build_manifest(doc_root, out_path)


if __name__ == "__main__":
    main()
