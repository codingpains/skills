#!/usr/bin/env bash
# Install this repo's skills and agents for Claude Code, Codex, or both.
#
#   ./install.sh              install both runtimes (default; edits are live)
#   ./install.sh --target codex|claude|both
#   ./install.sh --copy       copy instead of symlink (a frozen snapshot)
#   ./install.sh --status     show what is installed and how
#   ./install.sh --uninstall  remove everything this repo installed
#   ./install.sh --force      replace a same-named skill or agent that this repo
#                             did not install (the old one is backed up first)
#
# Claude: skills/* -> ~/.claude/skills; agents/*.md -> ~/.claude/agents
# Codex:  team-lead -> ~/.agents/skills; codex/agents/*.toml -> ~/.codex/agents
#         agents/*.md -> ~/.codex/agents/team-lead-playbooks
#
# Set CLAUDE_DIR, CODEX_DIR or CODEX_SKILLS_DIR to override a destination.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
CODEX_DIR="${CODEX_DIR:-$HOME/.codex}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
CLAUDE_MANIFEST="$CLAUDE_DIR/.skills-repo-manifest"
CODEX_MANIFEST="$CODEX_DIR/.skills-repo-manifest"
STAMP="$(date +%Y%m%d-%H%M%S)"

MODE=link
FORCE=0
TARGET=both
while [ "$#" -gt 0 ]; do
  arg="$1"
  case "$arg" in
    --copy) MODE=copy ;;
    --status) MODE=status ;;
    --uninstall) MODE=uninstall ;;
    --force) FORCE=1 ;;
    --target)
      shift
      [ "$#" -gt 0 ] || { echo "--target needs codex, claude or both" >&2; exit 2; }
      TARGET="$1"
      case "$TARGET" in codex|claude|both) ;; *) echo "unknown target: $TARGET" >&2; exit 2 ;; esac
      ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents" \
  "$CODEX_DIR/agents/team-lead-playbooks" "$CODEX_SKILLS_DIR"
touch "$CLAUDE_MANIFEST" "$CODEX_MANIFEST"

# Every selected item as source, destination, manifest and backup directory.
items() {
  local dir file
  if [ "$TARGET" = claude ] || [ "$TARGET" = both ]; then
    for dir in "$REPO"/skills/*/; do
      [ -f "$dir/SKILL.md" ] || continue
      dir="${dir%/}"
      printf '%s\t%s\t%s\t%s\n' "$dir" "$CLAUDE_DIR/skills/$(basename "$dir")" \
        "$CLAUDE_MANIFEST" "$CLAUDE_DIR/backups/skills-repo/$STAMP"
    done
    for file in "$REPO"/agents/*.md; do
      [ -f "$file" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$file" "$CLAUDE_DIR/agents/$(basename "$file")" \
        "$CLAUDE_MANIFEST" "$CLAUDE_DIR/backups/skills-repo/$STAMP"
    done
  fi
  if [ "$TARGET" = codex ] || [ "$TARGET" = both ]; then
    printf '%s\t%s\t%s\t%s\n' "$REPO/skills/team-lead" "$CODEX_SKILLS_DIR/team-lead" \
      "$CODEX_MANIFEST" "$CODEX_DIR/backups/skills-repo/$STAMP"
    for file in "$REPO"/codex/agents/*.toml; do
      [ -f "$file" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$file" "$CODEX_DIR/agents/$(basename "$file")" \
        "$CODEX_MANIFEST" "$CODEX_DIR/backups/skills-repo/$STAMP"
    done
    for file in "$REPO"/agents/team-*.md; do
      [ -f "$file" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$file" "$CODEX_DIR/agents/team-lead-playbooks/$(basename "$file")" \
        "$CODEX_MANIFEST" "$CODEX_DIR/backups/skills-repo/$STAMP"
    done
  fi
}

points_into_repo() { [ -L "$1" ] && case "$(readlink "$1")" in "$REPO"/*) return 0 ;; esac; return 1; }
in_manifest() { grep -qxF "$1" "$2"; }
manifest_add() { in_manifest "$1" "$2" || echo "$1" >> "$2"; }
manifest_remove() { grep -vxF "$1" "$2" > "$2.tmp" || true; mv "$2.tmp" "$2"; }

# Is the destination ours to replace?
ours() { points_into_repo "$1" || in_manifest "$1" "$2"; }

backup() {
  mkdir -p "$2"
  mv "$1" "$2/"
  echo "  backed up $1 -> $2/"
}

install_item() {
  local src="$1" dest="$2" manifest="$3" backup_dir="$4"
  mkdir -p "$(dirname "$dest")" "$(dirname "$manifest")"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$MODE" = link ] && [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
      echo "ok      $dest"
      return
    fi
    if ours "$dest" "$manifest"; then
      rm -rf "$dest"
    elif [ "$FORCE" = 1 ]; then
      backup "$dest" "$backup_dir"
    else
      echo "SKIP    $dest exists and was not installed by this repo (use --force)" >&2
      return
    fi
  fi
  if [ "$MODE" = link ]; then
    ln -s "$src" "$dest"
    manifest_remove "$dest" "$manifest"
    echo "linked  $dest -> $src"
  else
    cp -R "$src" "$dest"
    manifest_add "$dest" "$manifest"
    echo "copied  $dest"
  fi
}

# Remove links into this repo whose source is gone (a renamed or deleted skill).
prune() {
  local dest
  for dest in "$CLAUDE_DIR"/skills/* "$CLAUDE_DIR"/agents/* \
    "$CODEX_SKILLS_DIR"/team-lead "$CODEX_DIR"/agents/team-*.toml \
    "$CODEX_DIR"/agents/team-lead-playbooks/team-*.md; do
    if points_into_repo "$dest" && [ ! -e "$dest" ]; then
      rm "$dest"
      echo "pruned  $dest (source no longer in repo)"
    fi
  done
}

status() {
  local src dest manifest backup_dir state
  while IFS=$'\t' read -r src dest manifest backup_dir; do
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then state="linked"
    elif in_manifest "$dest" "$manifest" && [ -e "$dest" ]; then state="copied"
    elif [ -e "$dest" ]; then state="CONFLICT (not from this repo)"
    else state="not installed"
    fi
    printf '%-30s %s\n' "$state" "$dest"
  done < <(items)
}

uninstall() {
  local src dest manifest backup_dir
  while IFS=$'\t' read -r src dest manifest backup_dir; do
    if points_into_repo "$dest" || in_manifest "$dest" "$manifest"; then
      if [ -e "$dest" ] || [ -L "$dest" ]; then rm -rf "$dest"; echo "removed $dest"; fi
      manifest_remove "$dest" "$manifest"
    fi
  done < <(items)
}

case "$MODE" in
  status) status ;;
  uninstall) uninstall ;;
  link|copy)
    "$REPO/scripts/validate.sh"
    while IFS=$'\t' read -r src dest manifest backup_dir; do
      install_item "$src" "$dest" "$manifest" "$backup_dir"
    done < <(items)
    prune
    echo "Done. Start a new $TARGET session to pick up new or renamed skills and agents."
    ;;
esac
