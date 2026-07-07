#!/usr/bin/env sh
set -eu

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

warn() {
  echo "WARNING: $1" >&2
}

require_file() {
  path="$1"
  [ -f "$path" ] || fail "required file missing: $path"
}

echo "Running basic wiki validation..."

require_file "CLAUDE.md"
require_file "wiki/index.md"
require_file "wiki/log.md"
require_file "schema/lint-rules.md"

[ -d "raw" ] || fail "required directory missing: raw"
[ -d "wiki" ] || fail "required directory missing: wiki"
[ -d "schema" ] || fail "required directory missing: schema"

# If git is available and the workspace is a git repo, block edits to existing
# raw files. New raw files are allowed; modifications and deletions are not.
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  raw_changed="$(git diff --name-status -- raw/ || true)"
  if [ -n "$raw_changed" ]; then
    echo "$raw_changed" | while IFS= read -r line; do
      [ -n "$line" ] || continue
      status="$(printf '%s' "$line" | awk '{print $1}')"
      path="$(printf '%s' "$line" | awk '{print $2}')"
      case "$status" in
        A)
          ;;
        *)
          fail "raw content must be append-only; detected change: $status $path"
          ;;
      esac
    done
  fi
else
  warn "git repository not detected; raw change protection skipped"
fi

# Basic content checks for index and log.
if ! grep -qE "^# (Wiki Index|知识库导航)" wiki/index.md; then
  fail "wiki/index.md is missing the expected title"
fi

if ! grep -qE "^# (Wiki Log|知识库变更日志)" wiki/log.md; then
  fail "wiki/log.md is missing the expected title"
fi

# Ensure runtime hook location itself remains present.
[ -d ".claude/hooks" ] || fail "required directory missing: .claude/hooks"

echo "Basic wiki validation passed."
