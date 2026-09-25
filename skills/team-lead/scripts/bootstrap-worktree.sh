#!/usr/bin/env bash
# Give a new worktree the gitignored files a checkout needs to build and test,
# copied from the main checkout: every .env file and every dependency folder
# (node_modules, .venv, venv, vendor, .bundle). Folders are cloned
# copy-on-write where the filesystem supports it (APFS on macOS), so the copy
# is fast and shares disk until one side changes.
#
#   bootstrap-worktree.sh <main-checkout> <worktree>
#
# Anything already present in the worktree is left alone, so re-running is
# safe. Ends by naming each lockfile that differs between the two checkouts:
# the copied dependencies there may be stale, and that package needs its
# install command run in the worktree.
set -euo pipefail

SRC="${1:?usage: bootstrap-worktree.sh <main-checkout> <worktree>}"
DST="${2:?usage: bootstrap-worktree.sh <main-checkout> <worktree>}"
SRC="$(cd "$SRC" && pwd)"
DST="$(cd "$DST" && pwd)"

if [ "$SRC" = "$DST" ]; then
  echo "bootstrap: source and worktree are the same folder, nothing to do"
  exit 0
fi

# Copy-on-write clone when supported, plain copy otherwise.
clone() {
  cp -Rc "$1" "$2" 2>/dev/null || cp -R --reflink=auto "$1" "$2" 2>/dev/null || cp -R "$1" "$2"
}

ignored() { git -C "$SRC" ls-files --others --ignored --exclude-standard "$@"; }

# .env, .env.local, .env.development and the like, outside dependency folders.
ignored | grep -E '(^|/)\.env(\.[A-Za-z0-9_-]+)?$' | grep -vE '(^|/)(node_modules|\.venv|venv|vendor)/' \
  | while IFS= read -r file; do
      [ -e "$DST/$file" ] && continue
      mkdir -p "$DST/$(dirname "$file")"
      cp "$SRC/$file" "$DST/$file"
      chmod 600 "$DST/$file"
      echo "bootstrap: $file"
    done

# Dependency folders, top-most only: a node_modules inside a node_modules comes with its parent.
ignored --directory | grep -E '(^|/)(node_modules|\.venv|venv|vendor|\.bundle)/$' \
  | grep -vE '(node_modules|\.venv|venv|vendor)/.+' \
  | while IFS= read -r dir; do
      dir="${dir%/}"
      [ -e "$DST/$dir" ] && continue
      mkdir -p "$DST/$(dirname "$dir")"
      clone "$SRC/$dir" "$DST/$dir"
      echo "bootstrap: $dir/"
    done

# Lockfiles that differ: the copied dependencies may not match this branch.
stale=0
while IFS= read -r lock; do
  if [ ! -f "$SRC/$lock" ] || ! cmp -s "$SRC/$lock" "$DST/$lock"; then
    echo "bootstrap: lockfile differs from the main checkout, run install: $lock"
    stale=$((stale + 1))
  fi
done < <(git -C "$DST" ls-files -- \
  '*package-lock.json' '*yarn.lock' '*pnpm-lock.yaml' '*bun.lockb' \
  '*Gemfile.lock' '*poetry.lock' '*uv.lock' '*Pipfile.lock' '*go.sum' '*Cargo.lock' '*composer.lock')

[ "$stale" -eq 0 ] && echo "bootstrap: lockfiles match the main checkout"
exit 0
