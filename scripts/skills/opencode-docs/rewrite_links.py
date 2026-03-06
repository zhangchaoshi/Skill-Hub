#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, unquote


FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
URL_MAP: dict[str, str] = {}


@dataclass(frozen=True)
class LinkTarget:
    raw: str
    dest: str
    start: int
    end: int


def _toggle_fence(line: str, in_fence: bool) -> bool:
    if FENCE_RE.match(line):
        return not in_fence
    return in_fence


def _split_fragment(url: str) -> tuple[str, str]:
    if "#" not in url:
        return url, ""
    base, frag = url.split("#", 1)
    return base, f"#{frag}"


def _unescape_slashes(value: str) -> str:
    # Firecrawl output sometimes contains JSON-style escaped slashes in markdown links: "\/path"
    return value.replace("\\/", "/").replace("\\#", "#")


def _normalize_docs_url(target: str) -> str | None:
    """
    If target is an opencode docs zh-cn URL/path, normalize it to a path like:
      /docs/zh-cn[/...]
    Otherwise return None.
    """
    t = _unescape_slashes(target.strip())
    base, _frag = _split_fragment(t)

    if base.startswith("http://") or base.startswith("https://"):
        parsed = urlparse(base)
        if parsed.netloc not in {"opencode.ai", "www.opencode.ai"}:
            return None
        path = parsed.path
    elif base.startswith("/"):
        path = base
    else:
        return None

    if "?" in path:
        path = path.split("?", 1)[0]

    if not path.startswith("/docs/zh-cn"):
        # Also allow legacy absolute "/index.md" which points to the docs home
        if path == "/index.md":
            return "/index.md"
        return None

    # Remove trailing slash (except the root)
    if path != "/docs/zh-cn" and path.endswith("/"):
        path = path[:-1]

    return unquote(path)


def _load_url_map(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"url map must be a JSON object: {path}")
    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _extract_markdown_links(line: str) -> list[LinkTarget]:
    """
    Extract markdown inline links [text](dest) and images ![alt](dest).
    This parser is conservative: it doesn't try to implement full CommonMark,
    but it does handle <> destinations and balanced parentheses.
    """
    targets: list[LinkTarget] = []
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

        # Parse destination until matching ')', with support for:
        # - <...> wrapped destinations
        # - balanced parentheses inside
        if line[dest_start] == "<":
            gt = line.find(">", dest_start + 1)
            if gt == -1 or gt + 1 >= n or line[gt + 1] != ")":
                i = dest_start + 1
                continue
            dest = line[dest_start + 1 : gt]
            targets.append(LinkTarget(raw=line[dest_start : gt + 1], dest=dest, start=dest_start, end=gt + 1))
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
                    dest = line[dest_start:j].strip()
                    targets.append(LinkTarget(raw=dest, dest=dest, start=dest_start, end=j))
                    i = j + 1
                    break
                depth -= 1
            j += 1
        else:
            break

    return targets


def rewrite_file(file_path: Path, mirror_root: Path) -> tuple[int, int]:
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    in_fence = False
    changed_lines = 0
    total_rewrites = 0

    for idx, line in enumerate(lines):
        in_fence = _toggle_fence(line, in_fence)
        if in_fence:
            continue

        targets = _extract_markdown_links(line)
        if not targets:
            continue

        new_line = line
        # Rewrite from right to left to keep indices valid
        for t in reversed(targets):
            cleaned_dest = _unescape_slashes(t.dest)
            base, frag = _split_fragment(cleaned_dest)

            # Fix intra-page "index.md#..." links that should just be "#..."
            if base in {"index.md", "./index.md", "index.md/"}:
                replacement = frag if frag else "#_top"
                if t.raw.startswith("<") and t.raw.endswith(">"):
                    replacement = f"<{replacement}>"
                new_line = new_line[: t.start] + replacement + new_line[t.end :]
                total_rewrites += 1
                continue

            norm = _normalize_docs_url(base)
            if norm is None:
                if cleaned_dest != t.dest:
                    # At least fix the "\/" escaping.
                    replacement = f"{base}{frag}"
                    if t.raw.startswith("<") and t.raw.endswith(">"):
                        replacement = f"<{replacement}>"
                    new_line = new_line[: t.start] + replacement + new_line[t.end :]
                    total_rewrites += 1
                continue

            local_target = URL_MAP.get(norm)
            if not local_target:
                continue
            local_rel = Path(local_target)

            # current file relative to mirror root
            current_rel = file_path.relative_to(mirror_root)
            current_dir = current_rel.parent
            replacement_path = os.path.relpath(local_rel.as_posix(), start=current_dir.as_posix())
            replacement = f"{replacement_path}{frag}"

            # Preserve <> wrapper if originally used
            if t.raw.startswith("<") and t.raw.endswith(">"):
                replacement = f"<{replacement}>"

            new_line = new_line[: t.start] + replacement + new_line[t.end :]
            total_rewrites += 1

        if new_line != line:
            lines[idx] = new_line
            changed_lines += 1

    if changed_lines:
        file_path.write_text("".join(lines), encoding="utf-8")

    return changed_lines, total_rewrites


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite opencode zh-cn doc links to local relative paths.")
    parser.add_argument(
        "--root",
        required=True,
        help="Mirror root (e.g. skills/opencode-docs/references/opencode.ai/docs/zh-cn)",
    )
    parser.add_argument(
        "--map",
        required=True,
        help="URL map JSON (generated by organize_docs.py), mapping '/docs/zh-cn/...' -> local doc path",
    )
    args = parser.parse_args()

    mirror_root = Path(os.path.expanduser(args.root)).resolve()
    if not mirror_root.exists():
        raise SystemExit(f"Root does not exist: {mirror_root}")

    map_path = Path(os.path.expanduser(args.map)).resolve()
    if not map_path.exists():
        raise SystemExit(f"Map does not exist: {map_path}")

    global URL_MAP
    URL_MAP = _load_url_map(map_path)

    md_files = sorted(mirror_root.rglob("*.md"))
    changed_files = 0
    changed_lines_total = 0
    rewrites_total = 0
    for md in md_files:
        changed_lines, rewrites = rewrite_file(md, mirror_root)
        if changed_lines:
            changed_files += 1
            changed_lines_total += changed_lines
            rewrites_total += rewrites

    print(f"Root:          {mirror_root}")
    print(f"Markdown files:{len(md_files)}")
    print(f"Changed files: {changed_files}")
    print(f"Changed lines: {changed_lines_total}")
    print(f"Rewrites:      {rewrites_total}")


if __name__ == "__main__":
    main()
