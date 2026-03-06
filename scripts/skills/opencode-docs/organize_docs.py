#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Page:
    slug: str
    title: str
    url: str
    src_path: Path


INVALID_FILENAME_CHARS_RE = re.compile(r'[\/\\:\*\?"<>\|]+')


def _read_title(md_path: Path) -> str:
    for line in md_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    # fallback: slug
    return md_path.parent.name or md_path.stem


def _slug_to_url(slug: str) -> str:
    if slug == "":
        return "https://opencode.ai/docs/zh-cn"
    return f"https://opencode.ai/docs/zh-cn/{slug}"


def _collect_pages(raw_root: Path) -> dict[str, Page]:
    pages: dict[str, Page] = {}
    for md in raw_root.rglob("index.md"):
        rel = md.relative_to(raw_root)
        slug = "" if rel.as_posix() == "index.md" else "/".join(rel.parts[:-1])
        title = _read_title(md)
        pages[slug] = Page(slug=slug, title=title, url=_slug_to_url(slug), src_path=md)
    return pages


def _sanitize_filename(title: str) -> str:
    name = title.strip()
    name = INVALID_FILENAME_CHARS_RE.sub("-", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.replace(" ", "-")
    name = re.sub(r"-{2,}", "-", name).strip("-")
    if not name:
        return "untitled"
    return name


def _unique_name(desired: str, used: set[str]) -> str:
    if desired not in used:
        used.add(desired)
        return desired
    base, ext = os.path.splitext(desired)
    i = 2
    while True:
        candidate = f"{base}-{i}{ext}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        i += 1


def _write_page(dst_path: Path, page: Page) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    text = page.src_path.read_text(encoding="utf-8")
    header = f"<!-- source: {page.url} -->\n\n"
    if not text.startswith("<!-- source: "):
        text = header + text
    dst_path.write_text(text, encoding="utf-8")


def _safe_replace_dir(target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def organize(raw_root: Path, out_root: Path) -> tuple[dict[str, str], dict]:
    pages = _collect_pages(raw_root)

    # Map from slug to destination relative path (within out_root)
    mapping: dict[str, str] = {}
    used_paths: set[str] = set()

    def add(slug: str, dest_rel: str) -> None:
        if slug not in pages:
            return
        dest_rel = dest_rel.replace("\\", "/")
        dest_rel = _unique_name(dest_rel, used_paths)
        mapping[slug] = dest_rel

    def numbered(title: str, idx: int) -> str:
        safe = _sanitize_filename(title)
        return f"{idx:02d}-{safe}.md"

    # 官方侧边栏（按你截图的结构）的大致分组 + 顺序
    top_slugs = ["", "config", "providers", "network", "enterprise", "troubleshooting", "windows-wsl"]
    for i, slug in enumerate(top_slugs, start=1):
        if slug not in pages:
            continue
        add(slug, numbered(pages[slug].title, i))

    usage_slugs = [
        "tui",
        "cli",
        "ide",
        "keybinds",
        "share",
        "themes",
    ]
    for i, slug in enumerate(usage_slugs, start=1):
        if slug not in pages:
            continue
        add(slug, f"使用/{numbered(pages[slug].title, i)}")

    config_slugs = [
        "models",
        "permissions",
        "rules",
        "formatters",
        "tools",
        "custom-tools",
        "server",
        "web",
        "github",
        "gitlab",
    ]
    for i, slug in enumerate(config_slugs, start=1):
        if slug not in pages:
            continue
        add(slug, f"配置/{numbered(pages[slug].title, i)}")

    dev_slugs = [
        "agents",
        "skills",
        "plugins",
        "mcp-servers",
        "lsp",
        "sdk",
        "go",
        "acp",
        "zen",
        "ecosystem",
        "commands",
    ]
    for i, slug in enumerate(dev_slugs, start=1):
        if slug not in pages:
            continue
        add(slug, f"开发/{numbered(pages[slug].title, i)}")

    # Anything not mapped goes into "其他/<slug>.md"
    for slug in pages.keys():
        if slug in mapping:
            continue
        title = pages[slug].title or slug or "其他"
        safe = _sanitize_filename(title)
        slug_hint = slug.replace("/", "__") if slug else "root"
        add(slug, f"其他/{safe}-{slug_hint}.md")

    # Write output
    _safe_replace_dir(out_root)
    for slug, dest_rel in mapping.items():
        _write_page(out_root / dest_rel, pages[slug])

    # url_map maps normalized URL paths to local relative paths for link rewriting
    url_map: dict[str, str] = {}
    for slug, dest_rel in mapping.items():
        if slug == "":
            url_map["/docs/zh-cn"] = dest_rel
            url_map["/docs/zh-cn/"] = dest_rel
            url_map["/index.md"] = dest_rel
            url_map["/docs/zh-cn/index.md"] = dest_rel
        else:
            url_map[f"/docs/zh-cn/{slug}"] = dest_rel
            url_map[f"/docs/zh-cn/{slug}/"] = dest_rel

    nav = {
        "top": [
            {"title": pages[""].title if "" in pages else "简介", "path": mapping.get("", "01-简介.md")},
            {"title": pages["config"].title if "config" in pages else "配置", "path": mapping.get("config", "02-配置.md")},
            {"title": pages["providers"].title if "providers" in pages else "提供商", "path": mapping.get("providers", "03-提供商.md")},
            {"title": pages["network"].title if "network" in pages else "网络", "path": mapping.get("network", "04-网络.md")},
            {"title": pages["enterprise"].title if "enterprise" in pages else "企业版", "path": mapping.get("enterprise", "05-企业版.md")},
            {
                "title": pages["troubleshooting"].title if "troubleshooting" in pages else "故障排除",
                "path": mapping.get("troubleshooting", "06-故障排除.md"),
            },
            {"title": pages["windows-wsl"].title if "windows-wsl" in pages else "Windows", "path": mapping.get("windows-wsl", "07-Windows.md")},
        ],
        "sections": [
            {
                "title": "使用",
                "dir": "使用",
                "items": [{"title": pages[s].title, "path": mapping[s]} for s in usage_slugs if s in mapping],
            },
            {
                "title": "配置",
                "dir": "配置",
                "items": [
                    *[
                        {"title": pages[s].title, "path": mapping[s]}
                        for s in config_slugs
                        if s in mapping
                    ],
                ],
            },
            {
                "title": "开发",
                "dir": "开发",
                "items": [{"title": pages[s].title, "path": mapping[s]} for s in dev_slugs if s in mapping],
            },
        ],
    }

    return url_map, nav


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize opencode zh-cn markdown into an official-ish structure.")
    parser.add_argument("--from", dest="src", required=True, help="Raw docs root (from Firecrawl download)")
    parser.add_argument("--to", dest="dst", required=True, help="Destination doc root (repo-tracked)")
    parser.add_argument("--nav-out", required=True, help="Write nav JSON to this path")
    parser.add_argument("--url-map-out", required=True, help="Write URL->local map JSON to this path")
    args = parser.parse_args()

    src = Path(os.path.expanduser(args.src)).resolve()
    dst = Path(os.path.expanduser(args.dst)).resolve()
    nav_out = Path(os.path.expanduser(args.nav_out)).resolve()
    url_map_out = Path(os.path.expanduser(args.url_map_out)).resolve()

    if not src.exists():
        raise SystemExit(f"Source does not exist: {src}")

    url_map, nav = organize(src, dst)

    nav_out.parent.mkdir(parents=True, exist_ok=True)
    nav_out.write_text(json.dumps(nav, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    url_map_out.parent.mkdir(parents=True, exist_ok=True)
    url_map_out.write_text(json.dumps(url_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Organized docs into: {dst}")
    print(f"Wrote nav:          {nav_out}")
    print(f"Wrote url map:      {url_map_out} (entries: {len(url_map)})")


if __name__ == "__main__":
    main()
