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

tool_input = data.get("tool_input")
if not isinstance(tool_input, dict):
    sys.exit(0)
command = tool_input.get("command")
if not isinstance(command, str) or not command:
    sys.exit(0)

# 判定方針: コマンド文字列の部分一致は誤検知する(引用文字列内の語に反応する)ため、
# (1) 引用符の外の改行を区切りに変換し、ヒアドキュメント本文(実行されないデータ)を除去
# (2) shlex で引用符を尊重してトークン化し、演算子でセグメントに分割
# (3) git の push 呼び出しの refspec だけを見て main を対象にしているか判定する。
# 解析できないコマンド(引用符不整合など)と残余バイパス(コマンド置換・独自ラッパー・
# sudo -u 等のオプション付きプレフィックス)は許容して通す — 強制は git 層が担う。

PREFIXES = {"env", "sudo", "command", "nice", "nohup", "time", "xargs", "stdbuf", "timeout"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
PUSH_OPT_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
PUNCT = "();<>|&;"


def preprocess(cmd):
    """引用符の外にある改行を ';' に変換し、ヒアドキュメント本文を除去する。
    本文は実行されないデータであり、コマンドとして誤判定しないため。"""
    out = []
    i, n = 0, len(cmd)
    quote = ""
    pending = []  # 開始済みヒアドキュメントの終端語
    while i < n:
        ch = cmd[i]
        if quote:
            out.append(ch)
            if ch == quote and (quote == "'" or cmd[i - 1] != "\\"):
                quote = ""
            i += 1
        elif ch == "\\" and i + 1 < n:
            out.append(cmd[i:i + 2])
            i += 2
        elif ch in "'\"":
            quote = ch
            out.append(ch)
            i += 1
        elif cmd.startswith("<<", i) and not cmd.startswith("<<<", i):
            m = re.match(r"<<-?\s*(['\"]?)([A-Za-z0-9_]+)\1", cmd[i:])
            if m:
                pending.append(m.group(2))
                i += m.end()
            else:
                out.append(ch)
                i += 1
        elif ch == "\n":
            out.append(";")
            i += 1
            while pending:
                delim = pending.pop(0)
                while i < n:
                    eol = cmd.find("\n", i)
                    line = cmd[i:eol if eol != -1 else n]
                    i = (eol + 1) if eol != -1 else n
                    if line.strip() == delim:
                        break
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def tokenize(cmd):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=PUNCT)
    lex.whitespace_split = True
    try:
        return list(lex)
    except ValueError:
        # 引用符不整合など解析不能な場合は判定しない(素朴な分割へ退行すると
        # 引用文字列内の語で誤検知するため。強制は git 層が担う)
        return []


def segments(tokens):
    seg = []
    for t in tokens:
        if all(c in PUNCT for c in t):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(t)
    if seg:
        yield seg


def strip_prefixes(seg):
    i = 0
    stripped = False
    while i < len(seg):
        t = seg[i]
        if t in PREFIXES or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
            stripped = True
            i += 1
        elif stripped and t.startswith("-"):
            i += 1  # sudo -n 等、プレフィックス側のオプション(値までは追跡しない)
        else:
            break
    return seg[i:]


def shell_payload(seg):
    """bash -c / bash -lc 等の payload(実行される文字列)を返す。"""
    for j in range(1, len(seg) - 1):
        t = seg[j]
        if t == "-c" or (re.fullmatch(r"-[A-Za-z]+", t) and "c" in t):
            return seg[j + 1]
    return None


def push_refspecs(rest):
    """git の引数列から push サブコマンドの refspec 部分を返す。push でなければ None。"""
    i = 0
    while i < len(rest):
        t = rest[i]
        if t in GIT_GLOBAL_WITH_VALUE:
            i += 2
        elif t.startswith("-"):
            i += 1
        else:
            break
    if i >= len(rest) or rest[i] != "push":
        return None
    args = []
    j = i + 1
    while j < len(rest):
        t = rest[j]
        if t in PUSH_OPT_WITH_VALUE:
            j += 2
        elif t.startswith("-") and t != "-":
            j += 1
        else:
            args.append(t)
            j += 1
    return args[1:]  # 先頭はリモート名。以降が refspec


def targets_main(refspecs):
    for t in refspecs:
        base = t[1:] if t.startswith("+") else t
        if base in ("main", "refs/heads/main"):
            return True
        if base.endswith(":main") or base.endswith(":refs/heads/main"):
            return True
        if re.search(r":refs/[^\s:]+/main$", base):
            return True
    return False


def is_main_push(seg):
    seg = strip_prefixes(seg)
    if not seg:
        return False
    head = os.path.basename(seg[0])
    if head in SHELLS:
        payload = shell_payload(seg)
        return command_targets_main(payload) if payload else False
    if head != "git":
        return False
    refspecs = push_refspecs(seg[1:])
    return bool(refspecs) and targets_main(refspecs)


def command_targets_main(cmd):
    return any(is_main_push(s) for s in segments(tokenize(preprocess(cmd))))


if command_targets_main(command):
    print(
        "Blocked: pushing to main is not allowed. "
        "Push a feature branch and open a PR.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
PY
