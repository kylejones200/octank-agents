#!/usr/bin/env bash
# One-time per clone: route git hooks to scripts/git-hooks/ (repo-local, not .cursor).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository. Initialize with: git init" >&2
  exit 1
fi
git config core.hooksPath scripts/git-hooks
chmod +x scripts/git-hooks/pre-commit 2>/dev/null || true
chmod +x scripts/validate_registry.py 2>/dev/null || true
echo "core.hooksPath set to scripts/git-hooks (pre-commit runs validate_registry.py)."
