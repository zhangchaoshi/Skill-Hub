#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DOCS_FROM=".firecrawl/opencode.ai/docs/zh-cn"
DOCS_TO="skills/opencode-docs/references"

cd "$ROOT"

if [[ -z "${FIRECRAWL_API_KEY:-}" && -f "$ROOT/.env" ]]; then
  key_line="$(grep -E '^FIRECRAWL_API_KEY=' "$ROOT/.env" | head -n 1 || true)"
  if [[ -n "$key_line" ]]; then
    export FIRECRAWL_API_KEY="${key_line#FIRECRAWL_API_KEY=}"
  fi
fi

if [[ -z "${FIRECRAWL_API_KEY:-}" ]]; then
  echo "FIRECRAWL_API_KEY is not set."
  echo "Set it first, e.g.:"
  echo "  export FIRECRAWL_API_KEY='...'"
  echo "Or add a repo-local .env file containing:"
  echo "  FIRECRAWL_API_KEY=..."
  exit 2
fi

echo "[1/6] Firecrawl download..."
if [[ "${SKIP_DOWNLOAD:-0}" == "1" ]]; then
  if [[ ! -d "$DOCS_FROM" ]]; then
    echo "SKIP_DOWNLOAD=1 but missing: $DOCS_FROM"
    exit 3
  fi
  echo "SKIP_DOWNLOAD=1; reusing existing .firecrawl output."
else
  NPM_CONFIG_CACHE=/tmp/npm-cache NPM_CONFIG_LOGS_DIR=/tmp/npm-logs npx -y firecrawl-cli download "https://opencode.ai" \
    --include-paths "/docs/zh-cn" \
    --only-main-content \
    --limit 5000 \
    -y
fi

echo "[2/6] Import raw markdown to temp dir..."
raw_dir="$(mktemp -d /tmp/opencode-docs-raw.XXXXXX)"
meta_dir="$(mktemp -d /tmp/opencode-docs-meta.XXXXXX)"
NAV_JSON="$meta_dir/nav.json"
MAP_JSON="$meta_dir/url_map.json"
python3 "scripts/skills/opencode-docs/import_download.py" --from "$DOCS_FROM" --to "$raw_dir"

echo "[3/6] Organize docs into official-ish structure..."
python3 "scripts/skills/opencode-docs/organize_docs.py" \
  --from "$raw_dir" \
  --to "$DOCS_TO" \
  --nav-out "$NAV_JSON" \
  --url-map-out "$MAP_JSON"

echo "[4/6] Rewrite internal links to local relative paths..."
python3 "scripts/skills/opencode-docs/rewrite_links.py" --root "$DOCS_TO" --map "$MAP_JSON"

echo "[5/6] Download assets (images) and rewrite to local assets paths..."
python3 "scripts/skills/opencode-docs/download_assets.py" --root "$DOCS_TO" --assets "$DOCS_TO/assets"

echo "[6/6] Check links + refresh SKILL.md index..."
python3 "scripts/skills/opencode-docs/check_links.py" --root "$DOCS_TO"
python3 "scripts/skills/opencode-docs/build_skill_index.py" --skill "skills/opencode-docs/SKILL.md" --nav "$NAV_JSON"

echo "Done."
