#!/usr/bin/env bash
# Veridia 構造検証 — Skill規約・パス参照・installer の動作をプログラムで担保する
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

ng() { echo "NG: $*"; FAIL=1; }
section() { echo; echo "== $* =="; }

# --- 1. Skill規約(frontmatter・行数・references参照の実在) ---
section "Skill規約"
skill_total=0
for dir in "$ROOT"/skills/*/; do
  name="$(basename "$dir")"
  skill="$dir/SKILL.md"
  skill_total=$((skill_total + 1))

  if [ ! -f "$skill" ]; then
    ng "skills/$name/SKILL.md が存在しない"
    continue
  fi

  lines="$(wc -l < "$skill" | tr -d ' ')"
  [ "$lines" -le 100 ] || ng "skills/$name/SKILL.md が100行規約を超過(${lines}行)"

  head -1 "$skill" | grep -q '^---$' || ng "skills/$name/SKILL.md に frontmatter がない"

  fm_name="$(awk '/^---$/{c++; next} c==1 && /^name:/{print $2; exit}' "$skill")"
  [ "$fm_name" = "$name" ] || ng "skills/$name: frontmatter の name(${fm_name:-なし})がディレクトリ名と不一致"

  awk '/^---$/{c++; next} c==1 && /^description:/{found=1} END{exit !found}' "$skill" \
    || ng "skills/$name: frontmatter に description がない"

  # SKILL.md が参照する references/*.md が実在するか
  while IFS= read -r ref; do
    [ -f "$dir/$ref" ] || ng "skills/$name/SKILL.md が参照する $ref が存在しない"
  done < <(grep -oh 'references/[A-Za-z0-9._-]*\.md' "$skill" | sort -u)
done
echo "Skill: ${skill_total}本を検査"

# --- 1b. 前提規律ブロックの同一性(testing-with-genai を除く全Skillで一言一句同一) ---
section "前提規律の同一性"
expected_block=""
kiritsu_count=0
for dir in "$ROOT"/skills/*/; do
  name="$(basename "$dir")"
  [ "$name" = "testing-with-genai" ] && continue
  block="$(awk '/^## 前提規律/{f=1; print; next} /^## /{f=0} f' "$dir/SKILL.md")"
  if [ -z "$block" ]; then
    ng "skills/$name/SKILL.md に「前提規律」節がない"
    continue
  fi
  kiritsu_count=$((kiritsu_count + 1))
  if [ -z "$expected_block" ]; then
    expected_block="$block"
  elif [ "$block" != "$expected_block" ]; then
    ng "skills/$name の前提規律が他Skillと一致しない(ドリフト)"
  fi
done
echo "前提規律: ${kiritsu_count}本の同一性を検査"

# --- 2. テンプレート参照(SKILL内の quality/templates/* が正本 templates/ に実在) ---
section "テンプレート参照"
ref_total=0
while IFS= read -r ref; do
  ref_total=$((ref_total + 1))
  base="$(basename "$ref")"
  [ -f "$ROOT/templates/$base" ] || ng "Skillが参照する $ref の正本 templates/$base が存在しない"
done < <(grep -rhoe 'quality/templates/[A-Za-z0-9._-]*\.md' "$ROOT/skills" | sort -u)
echo "テンプレート参照: ${ref_total}件を検査"

# --- 3. installer の動作(一時ディレクトリへ導入して配置と参照解決を確認) ---
section "installer"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if ! "$ROOT/install.sh" "$TMP" > /dev/null 2>&1; then
  ng "install.sh の実行に失敗"
else
  src_skills="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
  dst_skills="$(find "$TMP/.claude/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
  [ "$src_skills" = "$dst_skills" ] || ng "導入されたSkill数が不一致(正本${src_skills} / 導入先${dst_skills})"

  for dir in "$ROOT"/skills/*/; do
    name="$(basename "$dir")"
    [ -f "$TMP/.claude/skills/$name/SKILL.md" ] || ng "導入先に .claude/skills/$name/SKILL.md がない"
  done

  src_templates="$(find "$ROOT/templates" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
  dst_templates="$(find "$TMP/quality/templates" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  [ "$src_templates" = "$dst_templates" ] || ng "導入されたテンプレート数が不一致(正本${src_templates} / 導入先${dst_templates})"

  [ -f "$TMP/quality/operating-model.md" ] || ng "導入先に quality/operating-model.md がない"

  # 導入先で、SKILL.md が参照する quality/templates/* が実際に解決するか
  while IFS= read -r ref; do
    [ -f "$TMP/$ref" ] || ng "導入先で $ref が解決しない"
  done < <(grep -rhoe 'quality/templates/[A-Za-z0-9._-]*\.md' "$TMP/.claude/skills" | sort -u)

  # 再実行しても安全か(冪等性)
  "$ROOT/install.sh" "$TMP" > /dev/null 2>&1 || ng "install.sh の再実行に失敗(冪等性)"

  # CLAUDE.md ポインタ(再実行後もマーカーブロックが1組だけ)
  begin_count="$(grep -cF '<!-- veridia:begin -->' "$TMP/CLAUDE.md" 2>/dev/null || echo 0)"
  [ "$begin_count" = "1" ] || ng "導入先 CLAUDE.md のマーカーブロックが1組でない(${begin_count}組)"
fi
echo "installer: 導入・配置・参照解決・再実行を検査"

# --- 4. installer(CLAUDE.md が AGENTS.md への symlink の構成) ---
section "installer(symlink構成)"
TMP2="$(mktemp -d)"
trap 'rm -rf "$TMP" "$TMP2"' EXIT
echo "# Agent Context" > "$TMP2/AGENTS.md"
ln -s AGENTS.md "$TMP2/CLAUDE.md"
if ! "$ROOT/install.sh" "$TMP2" > /dev/null 2>&1; then
  ng "symlink構成への install.sh の実行に失敗"
else
  [ -L "$TMP2/CLAUDE.md" ] || ng "CLAUDE.md の symlink が実体ファイルに置き換わった"
  grep -qF '<!-- veridia:begin -->' "$TMP2/AGENTS.md" || ng "ポインタが symlink 先の AGENTS.md に書かれていない"
  "$ROOT/install.sh" "$TMP2" > /dev/null 2>&1 || ng "symlink構成への再実行に失敗"
  begin_count2="$(grep -cF '<!-- veridia:begin -->' "$TMP2/AGENTS.md" || echo 0)"
  [ "$begin_count2" = "1" ] || ng "symlink構成でマーカーブロックが1組でない(${begin_count2}組)"
fi
echo "installer(symlink構成): symlink保持・ポインタ書き込み・冪等性を検査"

# --- 5. git hooks(.githooks/ の実行可否と動作) ---
section "git hooks"
for hook in pre-push pre-commit; do
  [ -x "$ROOT/.githooks/$hook" ] || ng ".githooks/$hook が存在しないか実行権限がない"
done

# pre-push: main への push を拒否し、それ以外は通すこと
if echo "refs/heads/feature abc refs/heads/main def" | "$ROOT/.githooks/pre-push" > /dev/null 2>&1; then
  ng "pre-push が main への push をブロックしない"
fi
echo "refs/heads/feature abc refs/heads/feature def" | "$ROOT/.githooks/pre-push" > /dev/null 2>&1 \
  || ng "pre-push が main 以外への push をブロックしてしまう"

# pre-commit: コンフリクトマーカーのステージを拒否し、通常の変更は通すこと
TMP3="$(mktemp -d)"
trap 'rm -rf "$TMP" "$TMP2" "$TMP3"' EXIT
git -C "$TMP3" init -q
printf '<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n' > "$TMP3/conflict.txt"
git -C "$TMP3" add conflict.txt
if (cd "$TMP3" && "$ROOT/.githooks/pre-commit" > /dev/null 2>&1); then
  ng "pre-commit がコンフリクトマーカーをブロックしない"
fi
git -C "$TMP3" rm -q --cached conflict.txt
printf 'clean content\n' > "$TMP3/clean.txt"
git -C "$TMP3" add clean.txt
(cd "$TMP3" && "$ROOT/.githooks/pre-commit" > /dev/null 2>&1) \
  || ng "pre-commit が通常の変更をブロックしてしまう"

# hooksPath の設定確認(clone毎の設定のため警告のみ)
hooks_path="$(git -C "$ROOT" config core.hooksPath 2>/dev/null || true)"
if [ "$hooks_path" != ".githooks" ]; then
  echo "警告: core.hooksPath が未設定です。有効化: git config core.hooksPath .githooks"
fi
echo "git hooks: pre-push / pre-commit の動作を検査"

# --- 6. Claude Code フック(pre-tool-use-policy.sh の判定精度) ---
section "Claude Code フック"
policy="$ROOT/.claude/hooks/pre-tool-use-policy.sh"
run_policy() {
  printf '{"tool_input":{"command":%s}}' "$1" | bash "$policy" > /dev/null 2>&1
}

# ブロックすべきもの(exit 2)
if run_policy '"git push --force origin main"'; then
  ng "policy が main への force push をブロックしない"
fi
if run_policy '"git push -f origin HEAD:main"'; then
  ng "policy が refspec 経由の force push をブロックしない"
fi
if run_policy '"git push origin +main"'; then
  ng "policy が +refspec の force push をブロックしない"
fi

# 通すべきもの(exit 0)— 実際に起きた誤検知の回帰テストを含む
run_policy '"git push -u origin feature-branch"' \
  || ng "policy が通常の push をブロックしてしまう"
run_policy '"git push --force origin feature-branch"' \
  || ng "policy が main 以外への force push をブロックしてしまう"
run_policy '"gh pr edit 1 --body-file body.md # 本文に --force-templates と git push main の文字列を含む"' \
  || ng "policy がコマンド文字列の部分一致で誤検知する(回帰)"
echo "Claude Code フック: ブロック3件・許可3件の判定を検査"

echo
if [ "$FAIL" -ne 0 ]; then
  echo "検証失敗"
  exit 1
fi
echo "検証成功: すべてのチェックを通過"
