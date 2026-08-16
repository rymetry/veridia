#!/usr/bin/env bash
# Claude Code 用の追加防御層: main への push をブロックする
# 強制の正本は .githooks/pre-push と GitHub の branch protection(こちらは早期警告)。
# git 層と同じ不変条件(main への push 禁止)を守る。force 判定はしない。
set -uo pipefail

# ヒアドキュメントは stdin を占有するため、フックへの入力JSONは先に bash で受けて
# 環境変数で渡す(python3 - <<EOF の中で sys.stdin は読めない)
HOOK_INPUT="$(cat)" export HOOK_INPUT

python3 - <<'PY'
import json
import os
import re
import sys
import shlex

try:
    data = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except json.JSONDecodeError:
    sys.exit(0)

command = (data.get("tool_input") or {}).get("command") or ""
if not command:
    sys.exit(0)

# 判定方針: コマンド文字列の部分一致は誤検知する(引用文字列内の語に反応する)ため、
# shlex で引用符を尊重してトークン化し、演算子でセグメントに分割してから
# 「git の push 呼び出しが main を対象にしているか」だけを見る。
# sh/bash -c 'payload' は payload を再帰解析する。
# 残余バイパス(コマンド置換・独自ラッパー等)は許容する — 強制は git 層が担う。

SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
OPERATORS = {";", ";;", "&&", "||", "|", "&"}


def tokenize(cmd):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars="();<>|&;")
    lex.whitespace_split = True
    try:
        return list(lex)
    except ValueError:
        return cmd.split()


def segments(tokens):
    seg = []
    for t in tokens:
        if t in OPERATORS or all(c in "();<>|&;" for c in t):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(t)
    if seg:
        yield seg


def is_main_push(seg):
    # env / VAR=value の前置を剥がす
    i = 0
    while i < len(seg) and (
        seg[i] == "env" or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[i])
    ):
        i += 1
    seg = seg[i:]
    if not seg:
        return False

    head = os.path.basename(seg[0])
    if head in SHELLS:
        # bash -c "..." は実行される payload なので再帰解析する
        for j in range(1, len(seg) - 1):
            if seg[j] == "-c":
                return command_targets_main(seg[j + 1])
        return False
    if head != "git":
        return False

    rest = seg[1:]
    pushish = "push" in rest or any(
        re.match(r"^alias\.[^=]+=.*push", t) for t in rest
    )
    if not pushish:
        return False
    return any(
        t in ("main", "refs/heads/main", "+main", "+refs/heads/main")
        or t.endswith(":main")
        or t.endswith(":refs/heads/main")
        for t in rest
    )


def command_targets_main(cmd):
    return any(is_main_push(seg) for seg in segments(tokenize(cmd)))


if command_targets_main(command):
    print(
        "Blocked: pushing to main is not allowed. "
        "Push a feature branch and open a PR.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
PY
