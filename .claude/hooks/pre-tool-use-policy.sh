#!/usr/bin/env bash
# Claude Code 用の追加防御層: main への force push をブロックする
# 強制の正本は .githooks/pre-push と GitHub の branch protection(こちらは早期警告)
set -uo pipefail

# ヒアドキュメントは stdin を占有するため、フックへの入力JSONは先に bash で受けて
# 環境変数で渡す(python3 - <<EOF の中で sys.stdin は読めない)
HOOK_INPUT="$(cat)" export HOOK_INPUT

python3 - <<'PY'
import json
import os
import re
import shlex
import sys

try:
    data = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except json.JSONDecodeError:
    sys.exit(0)

command = (data.get("tool_input") or {}).get("command") or ""
if not command:
    sys.exit(0)

# コマンド文字列全体の部分一致は誤検知する(例: PR本文に "--force-templates" や
# "git push ... main" が含まれるだけで発火)。連結コマンドを分割し、
# git push の呼び出し単位でトークン判定する。
for segment in re.split(r"&&|\|\||;|\|", command):
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if "git" not in tokens:
        continue
    rest = tokens[tokens.index("git") + 1:]
    if "push" not in rest:
        continue

    force = any(
        t in ("-f", "--force") or t.startswith("--force-with-lease")
        for t in rest
    )
    main_target = any(
        t in ("main", "refs/heads/main")
        or t.endswith(":main")
        or t.endswith(":refs/heads/main")
        for t in rest
    )
    plus_refspec = any(
        t.startswith("+")
        and (t[1:] in ("main", "refs/heads/main")
             or t.endswith(":main")
             or t.endswith(":refs/heads/main"))
        for t in rest
    )

    if (force and main_target) or plus_refspec:
        print("Blocked: force push to main is not allowed.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
PY
