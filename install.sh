#!/usr/bin/env bash
# Install this repo's skills and agents into ~/.claude so Claude Code can use them.
#
#   ./install.sh              symlink every skill and agent (default; edits are live)
#   ./install.sh --copy       copy instead of symlink (a frozen snapshot)
#   ./install.sh --status     show what is installed and how
#   ./install.sh --uninstall  remove everything this repo installed
#   ./install.sh --force      replace a same-named skill or agent that this repo
#                             did not install (the old one is backed up first)
#
# Skills:  skills/<name>/SKILL.md  ->  ~/.claude/skills/<name>
# Agents:  agents/<name>.md        ->  ~/.claude/agents/<name>.md
#
# Set CLAUDE_DIR to install somewhere other than ~/.claude.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
MANIFEST="$CLAUDE_DIR/.skills-repo-manifest"
BACKUP_DIR="$CLAUDE_DIR/backups/skills-repo/$(date +%Y%m%d-%H%M%S)"

MODE=link
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --copy) MODE=copy ;;
    --status) MODE=status ;;
    --uninstall) MODE=uninstall ;;
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents"
touch "$MANIFEST"

# Every installable item as "source<TAB>destination".
items() {
  local dir file
  for dir in "$REPO"/skills/*/; do
    [ -f "$dir/SKILL.md" ] || continue
    dir="${dir%/}"
    printf '%s\t%s\n' "$dir" "$CLAUDE_DIR/skills/$(basename "$dir")"
  done
  for file in "$REPO"/agents/*.md; do
    [ -f "$file" ] || continue
    printf '%s\t%s\n' "$file" "$CLAUDE_DIR/agents/$(basename "$file")"
  done
}

points_into_repo() { [ -L "$1" ] && case "$(readlink "$1")" in "$REPO"/*) return 0 ;; esac; return 1; }
in_manifest() { grep -qxF "$1" "$MANIFEST"; }
manifest_add() { in_manifest "$1" || echo "$1" >> "$MANIFEST"; }
manifest_remove() { grep -vxF "$1" "$MANIFEST" > "$MANIFEST.tmp" || true; mv "$MANIFEST.tmp" "$MANIFEST"; }

# Is the destination ours to replace?
ours() { points_into_repo "$1" || in_manifest "$1"; }

backup() {
  mkdir -p "$BACKUP_DIR"
  mv "$1" "$BACKUP_DIR/"
  echo "  backed up $1 -> $BACKUP_DIR/"
}

install_item() {
  local src="$1" dest="$2"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$MODE" = link ] && [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
      echo "ok      $dest"
      return
    fi
    if ours "$dest"; then
      rm -rf "$dest"
    elif [ "$FORCE" = 1 ]; then
      backup "$dest"
    else
      echo "SKIP    $dest exists and was not installed by this repo (use --force)" >&2
      return
    fi
  fi
  if [ "$MODE" = link ]; then
    ln -s "$src" "$dest"
    manifest_remove "$dest"
    echo "linked  $dest -> $src"
  else
    cp -R "$src" "$dest"
    manifest_add "$dest"
    echo "copied  $dest"
  fi
}

# Remove links into this repo whose source is gone (a renamed or deleted skill).
prune() {
  local dest
  for dest in "$CLAUDE_DIR"/skills/* "$CLAUDE_DIR"/agents/*; do
    if points_into_repo "$dest" && [ ! -e "$dest" ]; then
      rm "$dest"
      echo "pruned  $dest (source no longer in repo)"
    fi
  done
}

status() {
  local src dest state
  while IFS=$'\t' read -r src dest; do
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then state="linked"
    elif in_manifest "$dest" && [ -e "$dest" ]; then state="copied"
    elif [ -e "$dest" ]; then state="CONFLICT (not from this repo)"
    else state="not installed"
    fi
    printf '%-30s %s\n' "$state" "$dest"
  done < <(items)
}

uninstall() {
  local dest
  for dest in "$CLAUDE_DIR"/skills/* "$CLAUDE_DIR"/agents/*; do
    if points_into_repo "$dest"; then rm "$dest"; echo "removed $dest"; fi
  done
  while read -r dest; do
    [ -n "$dest" ] || continue
    if [ -e "$dest" ]; then rm -rf "$dest"; echo "removed $dest"; fi
  done < "$MANIFEST"
  : > "$MANIFEST"
}

case "$MODE" in
  status) status ;;
  uninstall) uninstall ;;
  link|copy)
    "$REPO/scripts/validate.sh"
    while IFS=$'\t' read -r src dest; do install_item "$src" "$dest"; done < <(items)
    prune
    echo "Done. Start a new Claude Code session to pick up new or renamed skills and agents."
    ;;
esac
