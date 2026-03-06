#!/usr/bin/env bash
set -euo pipefail

# Back-compat wrapper: scripts are centralized under scripts/skills/<skill-name>/
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec bash "$ROOT/scripts/skills/opencode-docs/update.sh"

