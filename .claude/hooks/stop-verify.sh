#!/usr/bin/env bash
# セッション終了時の検証: コンフリクトマーカーの残留を検出する
# ラベル付きの実マーカー(<<<<<<< HEAD 等)に一致させる。======= 単独は
# Markdown の見出し下線と衝突するため対象にしない(.githooks/pre-commit と同方針)
set -uo pipefail

matches="$(git --no-pager grep -nE '^(<{7}|>{7}|\|{7})( |$)' -- ':!node_modules' 2>/dev/null || true)"
if [ -n "$matches" ]; then
  echo "Conflict markers found:" >&2
  printf '%s\n' "$matches" >&2
  exit 2
fi

exit 0
