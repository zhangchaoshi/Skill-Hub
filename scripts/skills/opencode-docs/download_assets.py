#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, unquote


FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
IMG_MD_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
IMG_HTML_RE = re.compile(r"<img[^>]+src=['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE)
REF_DEF_RE = re.compile(r"^\s*\[[^\]]+]:\s*(\S+)\s*$")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp", ".ico"}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://opencode.ai/",
}


def _toggle_fence(line: str, in_fence: bool) -> bool:
    if FENCE_RE.match(line):
        return not in_fence
    return in_fence


def _unescape_slashes(value: str) -> str:
    return value.replace("\\/", "/")


def _is_opencode_asset(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in {"opencode.ai", "www.opencode.ai"}:
        return False
    path = parsed.path
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTS:
        return True
    return False


def _asset_dest(assets_root: Path, url: str) -> Path:
    parsed = urlparse(url)
    path = unquote(parsed.path).lstrip("/")
    # Keep original path under assets/
    return assets_root / path


def _extract_asset_urls(md_path: Path) -> set[str]:
    urls: set[str] = set()
    in_fence = False
    for line in md_path.read_text(encoding="utf-8").splitlines():
        in_fence = _toggle_fence(line, in_fence)
        if in_fence:
            continue

        for m in IMG_MD_RE.finditer(line):
            u = _unescape_slashes(m.group(1).strip().strip("<>").split("#", 1)[0])
            if _is_opencode_asset(u):
                urls.add(u)

        for m in IMG_HTML_RE.finditer(line):
            u = _unescape_slashes(m.group(1).strip().split("#", 1)[0])
            if _is_opencode_asset(u):
                urls.add(u)

        m = REF_DEF_RE.match(line)
        if m:
            u = _unescape_slashes(m.group(1).strip().strip("<>").split("#", 1)[0])
            if _is_opencode_asset(u):
                urls.add(u)

    return urls


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req) as resp, open(tmp, "wb") as f:
            shutil.copyfileobj(resp, f)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _rewrite_assets_in_file(md_path: Path, assets_root: Path) -> int:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    in_fence = False
    rewrites = 0

    for idx, line in enumerate(lines):
        in_fence = _toggle_fence(line, in_fence)
        if in_fence:
            continue

        original = line
        # Rewrite markdown images: ![](...)
        def repl_md(m: re.Match) -> str:
            nonlocal rewrites
            raw = _unescape_slashes(m.group(1).strip())
            url = raw.strip("<>").split("#", 1)[0]
            frag = ""
            if "#" in raw:
                frag = "#" + raw.split("#", 1)[1]
            if not _is_opencode_asset(url):
                return m.group(0)
            dest = _asset_dest(assets_root, url)
            rel = os.path.relpath(dest.as_posix(), start=md_path.parent.as_posix()).replace("\\", "/")
            rewrites += 1
            return m.group(0).replace(m.group(1), f"{rel}{frag}")

        line = IMG_MD_RE.sub(repl_md, line)

        # Rewrite html <img src="">
        def repl_html(m: re.Match) -> str:
            nonlocal rewrites
            raw = _unescape_slashes(m.group(1).strip())
            url = raw.split("#", 1)[0]
            frag = ""
            if "#" in raw:
                frag = "#" + raw.split("#", 1)[1]
            if not _is_opencode_asset(url):
                return m.group(0)
            dest = _asset_dest(assets_root, url)
            rel = os.path.relpath(dest.as_posix(), start=md_path.parent.as_posix()).replace("\\", "/")
            rewrites += 1
            return m.group(0).replace(m.group(1), f"{rel}{frag}")

        line = IMG_HTML_RE.sub(repl_html, line)

        if line != original:
            lines[idx] = line

    if rewrites:
        md_path.write_text("".join(lines), encoding="utf-8")

    return rewrites


def main() -> None:
    parser = argparse.ArgumentParser(description="Download opencode.ai image assets referenced by markdown and rewrite to local paths.")
    parser.add_argument("--root", required=True, help="Docs root containing markdown files")
    parser.add_argument("--assets", required=True, help="Assets directory to store downloaded images")
    args = parser.parse_args()

    root = Path(os.path.expanduser(args.root)).resolve()
    assets = Path(os.path.expanduser(args.assets)).resolve()
    if not root.exists():
        raise SystemExit(f"Docs root does not exist: {root}")

    md_files = sorted(root.rglob("*.md"))
    urls: set[str] = set()
    for md in md_files:
        urls |= _extract_asset_urls(md)

    downloaded = 0
    skipped = 0
    failed: list[str] = []
    for url in sorted(urls):
        dest = _asset_dest(assets, url)
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            continue
        try:
            _download(url, dest)
            downloaded += 1
        except urllib.error.HTTPError as e:
            failed.append(f"{url} ({e.code})")
        except Exception as e:
            failed.append(f"{url} ({type(e).__name__}: {e})")

    rewrites = 0
    for md in md_files:
        rewrites += _rewrite_assets_in_file(md, assets)

    print(f"Docs root:      {root}")
    print(f"Assets root:    {assets}")
    print(f"Assets found:   {len(urls)}")
    print(f"Downloaded:     {downloaded}")
    print(f"Skipped:        {skipped}")
    print(f"Failed:         {len(failed)}")
    print(f"Link rewrites:  {rewrites}")

    if failed:
        for item in failed[:25]:
            print(f"- {item}")
        if len(failed) > 25:
            print(f"... and {len(failed) - 25} more")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
