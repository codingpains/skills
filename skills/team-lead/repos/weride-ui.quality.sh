#!/usr/bin/env bash
# Local-only quality gates for weride-ui, which ships none of its own (no
# coverage provider, no complexity or duplication check). The tools install
# once into a cache outside the worktree, pinned to the worktree's vitest.
#
#   weride-ui.quality.sh <worktree> coverage <workspace> <test file>... -- <source file>...
#   weride-ui.quality.sh <worktree> complexity <file>...
#   weride-ui.quality.sh <worktree> dup <file or folder>...
#
#   coverage    runs the test files in <workspace> (apps/rider-app) with v8
#               coverage; prints line, branch and function percentages and the
#               uncovered lines of each source file (relative to the workspace).
#   complexity  cognitive complexity per function (sonarjs); prints every
#               function over 8 and fails over 15.
#   dup         copies of 5+ lines / 50+ tokens (jscpd) inside the paths given;
#               fails on any.
#
# Paths after the subcommand are relative to the worktree, except coverage's,
# which are relative to <workspace> like the workspace's own test script.
set -euo pipefail

usage="usage: weride-ui.quality.sh <worktree> coverage|complexity|dup ..."
WT="$(cd "${1:?$usage}" && pwd)"
CMD="${2:?$usage}"
shift 2
VITEST="$(node -p "require('$WT/node_modules/vitest/package.json').version")"
TOOLS="${XDG_CACHE_HOME:-$HOME/.cache}/team-lead/weride-ui-tools-vitest-$VITEST"

tools() {
  [ -x "$TOOLS/node_modules/.bin/jscpd" ] && return 0
  echo "quality: installing tools into $TOOLS (once)" >&2
  mkdir -p "$TOOLS"
  (cd "$TOOLS" && [ -f package.json ] || (cd "$TOOLS" && npm init -y >/dev/null))
  (cd "$TOOLS" && npm install --no-audit --no-fund --loglevel=error \
    "vitest@$VITEST" "@vitest/coverage-v8@$VITEST" \
    eslint@9 eslint-plugin-sonarjs@3 typescript-eslint@8 typescript@5 jscpd@4 >&2)
}

case "$CMD" in
  coverage)
    WS="${1:?coverage needs a workspace}"; shift
    TESTS=(); SOURCES=(); seen=0
    for a in "$@"; do
      if [ "$a" = "--" ]; then seen=1; elif [ $seen -eq 0 ]; then TESTS+=("$a"); else SOURCES+=("$a"); fi
    done
    [ ${#TESTS[@]} -gt 0 ] && [ ${#SOURCES[@]} -gt 0 ] || { echo "$usage" >&2; exit 2; }
    tools
    # vitest resolves its coverage provider from the project: link it in (node_modules is gitignored).
    mkdir -p "$WT/node_modules/@vitest"
    ln -sfn "$TOOLS/node_modules/@vitest/coverage-v8" "$WT/node_modules/@vitest/coverage-v8"
    OUT="$(mktemp -d)"
    mkdir -p "$OUT/cov"
    include=(); for s in "${SOURCES[@]}"; do include+=("--coverage.include=$s"); done
    (cd "$WT/$WS" && npx vitest run "${TESTS[@]}" --coverage.enabled --coverage.provider=v8 \
      --coverage.reporter=json --coverage.reportsDirectory="$OUT/cov" "${include[@]}" > "$OUT/vitest.log" 2>&1) \
      || { tail -n 30 "$OUT/vitest.log"; exit 1; }
    grep -E '^ +(Test Files|Tests) ' "$OUT/vitest.log"
    node -e '
      const data = require(process.argv[1]); const root = process.argv[2];
      for (const [file, f] of Object.entries(data)) {
        const pct = (h) => { const v = Object.values(h).flat(); return v.length ? (100 * v.filter((c) => c > 0).length / v.length).toFixed(1) + "%" : "n/a"; };
        const missed = [...new Set(Object.entries(f.s).filter(([, c]) => c === 0).map(([k]) => f.statementMap[k].start.line))].sort((a, b) => a - b);
        console.log(`${file.replace(root + "/", "")}: statements ${pct(f.s)}, branches ${pct(f.b)}, functions ${pct(f.f)}, uncovered lines ${JSON.stringify(missed)}`);
      }' "$OUT/cov/coverage-final.json" "$WT/$WS"
    ;;
  complexity)
    [ $# -gt 0 ] || { echo "$usage" >&2; exit 2; }
    tools
    cat > "$TOOLS/eslint.config.mjs" <<'EOF'
import tseslint from 'typescript-eslint'
import sonarjs from 'eslint-plugin-sonarjs'
export default [
  { files: ['**/*.{ts,tsx,js,jsx}'], languageOptions: { parser: tseslint.parser, parserOptions: { ecmaFeatures: { jsx: true } } },
    plugins: { sonarjs }, linterOptions: { reportUnusedDisableDirectives: 'off' },
    rules: { 'sonarjs/cognitive-complexity': ['warn', 8] } },
]
EOF
    OUT="$(mktemp -d)"
    status=0
    (cd "$WT" && "$TOOLS/node_modules/.bin/eslint" --no-config-lookup -c "$TOOLS/eslint.config.mjs" \
      --no-inline-config -f json -o "$OUT/eslint.json" "$@" 2> "$OUT/eslint.err") || status=$?
    # eslint exits 1 on warnings-as-findings, 2 on a crash or a path that matches nothing.
    [ "$status" -le 1 ] && [ -s "$OUT/eslint.json" ] || { cat "$OUT/eslint.err"; echo "complexity: eslint failed"; exit 1; }
    node -e '
      const res = require(process.argv[1]); const root = process.argv[2] + "/"; let over = 0, bad = 0;
      console.log(`complexity: ${res.length} files checked`);
      for (const r of res) for (const m of r.messages) {
        const at = `${r.filePath.replace(root, "")}:${m.line}`;
        if (m.ruleId === "sonarjs/cognitive-complexity") {
          const n = Number((m.message.match(/from (\d+)/) || [])[1]);
          console.log(`${at}: cognitive complexity ${n}`); if (n > 15) over++;
        } else { console.log(`${at}: ${m.message}`); bad++; }
      }
      if (bad) { console.log("complexity: files eslint could not analyse"); process.exit(1); }
      if (over) { console.log(`complexity: ${over} over 15 fails`); process.exit(1); }
      console.log("complexity: nothing over 15");' "$OUT/eslint.json" "$WT"
    ;;
  dup)
    [ $# -gt 0 ] || { echo "$usage" >&2; exit 2; }
    tools
    (cd "$WT" && "$TOOLS/node_modules/.bin/jscpd" --min-lines 5 --min-tokens 50 --reporters console \
      --ignore '**/node_modules/**,**/generated/**,**/.next/**,**/dist/**' --exitCode 1 "$@")
    ;;
  *) echo "$usage" >&2; exit 2 ;;
esac
