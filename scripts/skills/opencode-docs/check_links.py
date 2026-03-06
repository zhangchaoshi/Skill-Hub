#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


@dataclass(frozen=True)
class Link:
    target: str
    file: Path
    line_no: int


def _toggle_fence(line: str, in_fence: bool) -> bool:
    if FENCE_RE.match(line):
        return not in_fence
    return in_fence


def _split_fragment(target: str) -> str:
    return target.split("#", 1)[0]


def _is_external(target: str) -> bool:
    t = target.strip()
    return (
        t.startswith("http://")
        or t.startswith("https://")
        or t.startswith("mailto:")
        or t.startswith("tel:")
        or t.startswith("javascript:")
    )


def _extract_links_from_line(line: str) -> list[str]:
    # Simple extractor aligned with rewrite_links.py: [text](dest) and ![alt](dest)
    links: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        open_bracket = line.find("[", i)
        if open_bracket == -1:
            break
        close_bracket = line.find("]", open_bracket + 1)
        if close_bracket == -1:
            break
        if close_bracket + 1 >= n or line[close_bracket + 1] != "(":
            i = close_bracket + 1
            continue
        dest_start = close_bracket + 2
        if dest_start >= n:
            break
        if line[dest_start] == "<":
            gt = line.find(">", dest_start + 1)
            if gt == -1:
                i = dest_start + 1
                continue
            if gt + 1 < n and line[gt + 1] == ")":
                links.append(line[dest_start + 1 : gt].strip())
                i = gt + 2
                continue
        depth = 0
        j = dest_start
        while j < n:
            ch = line[j]
            if ch == "\\" and j + 1 < n:
                j += 2
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                if depth == 0:
                    links.append(line[dest_start:j].strip())
                    i = j + 1
                    break
                depth -= 1
            j += 1
        else:
            break
    return links


def _iter_markdown_links(root: Path) -> list[Link]:
    results: list[Link] = []
    for md in root.rglob("*.md"):
        in_fence = False
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), start=1):
            in_fence = _toggle_fence(line, in_fence)
            if in_fence:
                continue
            for target in _extract_links_from_line(line):
                results.append(Link(target=target, file=md, line_no=i))
    return results


def _check_manifest(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return [f"Manifest must be a JSON array: {manifest_path}"]
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            errors.append(f"Manifest entry {idx} is not an object")
            continue
        local_path = entry.get("local_path")
        url = entry.get("url")
        if not local_path or not isinstance(local_path, str):
            errors.append(f"Manifest entry {idx} missing local_path")
            continue
        p = manifest_path.parent / local_path
        if not p.exists():
            errors.append(f"Missing file for manifest entry {idx}: {p} (url={url})")
    return errors


def _check_local_links(root: Path) -> list[str]:
    errors: list[str] = []
    links = _iter_markdown_links(root)
    for link in links:
        target = link.target.strip()
        if not target or target == "#":
            continue
        if _is_external(target):
            continue
        base = _split_fragment(target)
        if not base:
            continue
        # Ignore pure anchors
        if target.startswith("#"):
            continue
        # Ignore special scheme-like targets
        if ":" in base and not base.startswith(("./", "../")):
            continue

        # Resolve against the file directory
        resolved = (link.file.parent / base).resolve()
        if not resolved.exists():
            errors.append(f"Broken link: {link.file}:{link.line_no} -> {target}")
            continue
        if resolved.is_dir():
            # Prefer index.md for directory targets
            idx = resolved / "index.md"
            if not idx.exists():
                errors.append(f"Directory link without index.md: {link.file}:{link.line_no} -> {target}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate manifest files exist and local rewritten links are resolvable.")
    parser.add_argument(
        "--root",
        required=True,
        help="Mirror root (e.g. skills/opencode-docs/references/opencode.ai/docs/zh-cn)",
    )
    parser.add_argument(
        "--manifest",
        required=False,
        help="Optional manifest path (if provided, verify all listed files exist)",
    )
    args = parser.parse_args()

    root = Path(os.path.expanduser(args.root)).resolve()

    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")

    errors: list[str] = []
    if args.manifest:
        manifest = Path(os.path.expanduser(args.manifest)).resolve()
        if not manifest.exists():
            raise SystemExit(f"Manifest does not exist: {manifest}")
        errors.extend(_check_manifest(manifest))
    errors.extend(_check_local_links(root))

    if errors:
        print("FAILED")
        for e in errors[:200]:
            print(f"- {e}")
        if len(errors) > 200:
            print(f"... and {len(errors) - 200} more")
        raise SystemExit(1)

    print("OK")


if __name__ == "__main__":
    main()
