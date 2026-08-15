#!/usr/bin/env bash
# Veridia installer — skills/ を正本として対象プロジェクトへ導入する
set -euo pipefail

usage() {
  cat <<'USAGE'
使い方: ./install.sh <対象プロジェクトのパス> [--force-templates]

  <対象プロジェクトのパス>  導入先リポジトリのルート
  --force-templates         既存の quality/templates/ と quality/operating-model.md を上書きする

導入内容:
  skills/                 → <対象>/.claude/skills/     (常に正本と同期・上書き)
  templates/              → <対象>/quality/templates/  (既定では既存ファイルを保持)
  docs/operating-model.md → <対象>/quality/operating-model.md (同上)
  CLAUDE.md               → 前提規律へのポインタをマーカーブロックで追記・同期
USAGE
}

err() { echo "エラー: $*" >&2; exit 1; }

TARGET=""
FORCE_TEMPLATES=0
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --force-templates) FORCE_TEMPLATES=1 ;;
    -*) usage >&2; err "不明なオプション: $arg" ;;
    *)
      [ -z "$TARGET" ] || err "対象パスが複数指定されています: $TARGET と $arg"
      TARGET="$arg"
      ;;
  esac
done

if [ -z "$TARGET" ]; then
  usage >&2
  err "対象プロジェクトのパスを指定してください"
fi
[ -d "$TARGET" ] || err "対象が存在しないかディレクトリではありません: $TARGET"

SRC="$(cd "$(dirname "$0")" && pwd)"
TARGET="$(cd "$TARGET" && pwd)"
[ "$SRC" != "$TARGET" ] || err "Veridiaリポジトリ自身には導入できません"
[ -d "$SRC/skills" ] || err "skills/ が見つかりません(Veridiaリポジトリのルートから実行してください)"
[ -d "$SRC/templates" ] || err "templates/ が見つかりません"
[ -f "$SRC/docs/operating-model.md" ] || err "docs/operating-model.md が見つかりません"

if [ ! -e "$TARGET/.git" ]; then
  echo "注意: $TARGET は git リポジトリではありません。そのまま続行します。" >&2
fi

# 1. skills → .claude/skills(正本はVeridia。常に同期)
mkdir -p "$TARGET/.claude/skills"
skill_count=0
for dir in "$SRC"/skills/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || err "SKILL.md がありません: skills/$name"
  rm -rf "${TARGET:?}/.claude/skills/${name:?}"
  cp -R "$dir" "$TARGET/.claude/skills/$name"
  skill_count=$((skill_count + 1))
done
echo "skills: ${skill_count}本を .claude/skills/ へ同期しました"

# 既定では既存ファイルを保持してコピーする(--force-templates で上書き)
copy_keep_existing() {
  local src="$1" dest="$2"
  if [ -f "$dest" ] && [ "$FORCE_TEMPLATES" -eq 0 ]; then
    if ! cmp -s "$src" "$dest"; then
      echo "保持: ${dest#"$TARGET"/}(既存と差分あり。上書きは --force-templates)" >&2
    fi
    return 1
  fi
  cp "$src" "$dest"
}

# 2. templates → quality/templates
mkdir -p "$TARGET/quality/templates"
copied=0
kept=0
for f in "$SRC"/templates/*.md; do
  if copy_keep_existing "$f" "$TARGET/quality/templates/$(basename "$f")"; then
    copied=$((copied + 1))
  else
    kept=$((kept + 1))
  fi
done
echo "templates: ${copied}枚をコピー、${kept}枚を保持しました"

# 3. operating-model → quality/operating-model.md
if copy_keep_existing "$SRC/docs/operating-model.md" "$TARGET/quality/operating-model.md"; then
  echo "operating-model: quality/operating-model.md へコピーしました"
else
  echo "operating-model: 既存の quality/operating-model.md を保持しました"
fi

# 4. CLAUDE.md へ前提規律のポインタを追記(マーカーブロックは installer が管理・同期)
#    Skillを経由せず quality/ 配下を直接編集する場合の取りこぼしを防ぐ
MARKER_BEGIN='<!-- veridia:begin -->'
MARKER_END='<!-- veridia:end -->'
claude_md="$TARGET/CLAUDE.md"
if [ -e "$claude_md" ]; then
  # CLAUDE.md → AGENTS.md 等の symlink は実体へ解決してから書く(symlinkを壊さない)
  claude_md="$(readlink -f "$claude_md")"
  perl -0777 -i -pe \
    's/\n*\Q<!-- veridia:begin -->\E.*?\Q<!-- veridia:end -->\E\n*/\n/s; s/\s+\z/\n/' \
    "$claude_md"
fi
cat >> "$claude_md" <<BLOCK

$MARKER_BEGIN
<!-- このブロックは Veridia installer が管理する。手で編集しない -->
- \`quality/\` 配下の成果物(premortem.md、test-plan.md 等)を作成・編集するときは、
  \`.claude/skills/\` の該当Skillを起動し、その「前提規律(AIと作る成果物)」に従う。
$MARKER_END
BLOCK
echo "CLAUDE.md: 前提規律へのポインタを設定しました(${claude_md#"$TARGET"/})"

echo "完了。対象プロジェクトの Claude Code で /premortem から始められます(成果物は quality/ 配下)。"
