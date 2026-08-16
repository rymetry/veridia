#!/usr/bin/env bash
# Veridia 構造検証 — Skill規約・パス参照・installer の動作をプログラムで担保する
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0
VMARK_BEGIN='<!-- veridia:begin -->'  # install.sh の MARKER_BEGIN と一致させること

# 一時ディレクトリは単一のルート配下にまとめ、trap は1回だけ設定する
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

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

  # SKILL.md が参照する references/*.md が実在するか(../<skill>/references/ の
  # クロスSkill参照も、Skillディレクトリからの相対パスとして解決する)
  while IFS= read -r ref; do
    [ -f "$dir/$ref" ] || ng "skills/$name/SKILL.md が参照する $ref が存在しない"
  done < <(grep -ohE '(\.\./[A-Za-z0-9-]+/)?references/[A-Za-z0-9._-]+\.md' "$skill" | sort -u)
done
echo "Skill: ${skill_total}本を検査"

# --- 1b. 前提規律ブロックの同一性(testing-with-genai を除く全Skillで一言一句同一) ---
section "前提規律の同一性"
expected_block=""
kiritsu_count=0
for dir in "$ROOT"/skills/*/; do
  name="$(basename "$dir")"
  [ "$name" = "testing-with-genai" ] && continue
  [ -f "$dir/SKILL.md" ] || continue  # 欠損はセクション1がNGを記録済み(awkのexitで全体を止めない)
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
TMP="$WORK/basic"
mkdir -p "$TMP"

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
  begin_count="$(grep -cF "$VMARK_BEGIN" "$TMP/CLAUDE.md" 2>/dev/null || true)"
  [ "$begin_count" = "1" ] || ng "導入先 CLAUDE.md のマーカーブロックが1組でない(${begin_count:-0}組)"
fi
echo "installer: 導入・配置・参照解決・再実行を検査"

# --- 4. installer(CLAUDE.md が AGENTS.md への symlink の構成) ---
section "installer(symlink構成)"
TMP2="$WORK/claude-symlink"
mkdir -p "$TMP2"
echo "# Agent Context" > "$TMP2/AGENTS.md"
ln -s AGENTS.md "$TMP2/CLAUDE.md"
if ! "$ROOT/install.sh" "$TMP2" > /dev/null 2>&1; then
  ng "symlink構成への install.sh の実行に失敗"
else
  [ -L "$TMP2/CLAUDE.md" ] || ng "CLAUDE.md の symlink が実体ファイルに置き換わった"
  grep -qF "$VMARK_BEGIN" "$TMP2/AGENTS.md" || ng "ポインタが symlink 先の AGENTS.md に書かれていない"
  "$ROOT/install.sh" "$TMP2" > /dev/null 2>&1 || ng "symlink構成への再実行に失敗"
  begin_count2="$(grep -cF "$VMARK_BEGIN" "$TMP2/AGENTS.md" || true)"
  [ "$begin_count2" = "1" ] || ng "symlink構成でマーカーブロックが1組でない(${begin_count2:-0}組)"
fi
echo "installer(symlink構成): symlink保持・ポインタ書き込み・冪等性を検査"

# --- 4b. installer(危険構成の拒否) ---
section "installer(危険構成の拒否)"
TMP4="$WORK/selfhost"
TMP5="$WORK/badmarker"
mkdir -p "$TMP4" "$TMP5"

# .claude/skills が symlink の対象(Veridia同形の自己ホスト構成)には導入を拒否し、
# リンク先の正本を破壊しないこと。カナリアは正本と衝突する名前(premortem)にする
mkdir -p "$TMP4/skills/premortem" "$TMP4/.claude"
echo "original content" > "$TMP4/skills/premortem/SKILL.md"
ln -s ../skills "$TMP4/.claude/skills"
if out="$("$ROOT/install.sh" "$TMP4" 2>&1)"; then
  ng "installer が .claude/skills symlink 構成への導入を拒否しない"
elif ! echo "$out" | grep -q "symlink のため導入できません"; then
  ng "installer の拒否理由が期待と異なる: $out"
fi
[ "$(cat "$TMP4/skills/premortem/SKILL.md" 2>/dev/null)" = "original content" ] \
  || ng "installer が symlink 先の正本を破壊した"

# begin/end マーカーが不完全な CLAUDE.md への導入は、何も変更せずに失敗すること
printf '# X\n\n%s\nbroken\n' "$VMARK_BEGIN" > "$TMP5/CLAUDE.md"
cp "$TMP5/CLAUDE.md" "$WORK/badmarker-orig"
if out="$("$ROOT/install.sh" "$TMP5" 2>&1)"; then
  ng "installer が不完全なマーカーの CLAUDE.md への追記を拒否しない"
elif ! echo "$out" | grep -q "マーカーが不完全"; then
  ng "installer の拒否理由が期待と異なる: $out"
fi
cmp -s "$TMP5/CLAUDE.md" "$WORK/badmarker-orig" \
  || ng "installer が拒否したのに CLAUDE.md を変更した"
[ ! -e "$TMP5/quality" ] && [ ! -e "$TMP5/.claude" ] \
  || ng "installer が拒否したのに導入先へ書き込んだ(事前検証が導入後に走っている)"
echo "installer(危険構成の拒否): symlink拒否・正本保全・不完全マーカー時の無変更を検査"

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
TMP3="$WORK/githooks"
mkdir -p "$TMP3"
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
expect_block() { if run_policy "$1"; then ng "$2"; fi; }
expect_allow() { run_policy "$1" || ng "$2"; }

# ブロックすべきもの — ルールは git 層と同じ「main への push 禁止」
expect_block '"git push origin main"' "policy が main への push をブロックしない"
expect_block '"git push --force origin main"' "policy が main への force push をブロックしない"
expect_block '"git push -f origin HEAD:main"' "policy が refspec 経由の push をブロックしない"
expect_block '"git push origin +main"' "policy が +refspec の push をブロックしない"
expect_block '"/usr/bin/git push origin main"' "policy がパス指定の git をブロックしない(回帰)"
expect_block '"bash -c \"git push --force origin main\""' "policy が bash -c ラッパーをブロックしない(回帰)"
expect_block '"bash -lc \"git push origin main\""' "policy が結合オプション -lc をブロックしない(回帰)"
expect_block '"command git push origin main"' "policy が command プレフィックスをブロックしない(回帰)"
expect_block '"sudo git push --force origin main"' "policy が sudo プレフィックスをブロックしない(回帰)"

# 通すべきもの — 実際に起きた誤検知の回帰テストを含む
expect_allow '"git push -u origin feature-branch"' "policy が通常の push をブロックしてしまう"
expect_allow '"git push --force origin feature-branch"' "policy が main 以外への force push をブロックしてしまう"
expect_allow '"git pull origin main"' "policy が main からの pull をブロックしてしまう"
expect_allow '"git push main feature-branch"' "policy が main という名のリモートへの push をブロックしてしまう(回帰)"
expect_allow '"git stash push -m main"' "policy が git stash push をブロックしてしまう(回帰)"
expect_allow '"gh pr edit 1 --body-file body.md # 本文に --force-templates と git push main の文字列を含む"' \
  "policy がコマンド文字列の部分一致で誤検知する(回帰)"
expect_allow '"echo \"do not run: git push --force origin main\" | tee note.txt"' \
  "policy が引用文字列内の語で誤検知する(回帰: パイプ分割)"
expect_allow '"git commit -m \"memo; git push --force origin main is forbidden\""' \
  "policy がコミットメッセージ内の語で誤検知する(回帰: セミコロン分割)"
expect_allow '"git checkout main\ngit pull\ngit push -u origin feature-branch"' \
  "policy が複数行コマンドの行をまたいで誤検知する(回帰: 改行セパレータ)"
expect_allow '"git commit -m don'\''t push to main yet"' \
  "policy が引用符不整合のコマンドで誤検知する(回帰: fail-open)"
expect_allow '"cat > doc.md <<EOF\n禁止例: ; git push origin main\nEOF"' \
  "policy がヒアドキュメント本文で誤検知する(回帰: 本文はデータ)"
echo "Claude Code フック: ブロック9件・許可11件の判定を検査"

# stop-verify: ラベル付き実マーカーを検出し、Markdownの見出し下線(=======)には反応しないこと
stop_verify="$ROOT/.claude/hooks/stop-verify.sh"
TMP6="$WORK/stopverify"
mkdir -p "$TMP6"
git -C "$TMP6" init -q
printf 'x\n<<<<<<< HEAD\ny\n>>>>>>> branch\n' > "$TMP6/a.txt"
git -C "$TMP6" add a.txt
if (cd "$TMP6" && bash "$stop_verify" > /dev/null 2>&1); then
  ng "stop-verify がラベル付きコンフリクトマーカーを検出しない"
fi
git -C "$TMP6" rm -q --cached a.txt && rm "$TMP6/a.txt"
printf '見出し\n=======\n本文\n' > "$TMP6/b.md"
git -C "$TMP6" add b.md
(cd "$TMP6" && bash "$stop_verify" > /dev/null 2>&1) \
  || ng "stop-verify がMarkdownの見出し下線(=======)に誤反応する"
echo "stop-verify: 実マーカー検出と見出し下線の非検出を検査"

echo
if [ "$FAIL" -ne 0 ]; then
  echo "検証失敗"
  exit 1
fi
echo "検証成功: すべてのチェックを通過"
