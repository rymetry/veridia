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
fi
echo "installer: 導入・配置・参照解決・再実行を検査"

echo
if [ "$FAIL" -ne 0 ]; then
  echo "検証失敗"
  exit 1
fi
echo "検証成功: すべてのチェックを通過"
