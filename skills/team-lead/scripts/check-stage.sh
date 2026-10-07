#!/usr/bin/env bash
# The Lead's mechanical checks on one stage's report and its commits, so the
# Lead does not have to read the whole report or run each git command itself.
#
#   check-stage.sh <worktree> <base-sha> <report-file>
#
# The stage is the report file's name up to its first dash (coder-b2.md is a
# coder report). Prints one line per check, "ok" or "FAIL", and exits 1 when
# any check fails:
#   report    the file exists, has every stage-report.md section and the
#             Stage-specific lines its agent file names, and is not BLOCKED
#   commits   every commit the report lists is in <base>..HEAD
#   attrib    no commit in <base>..HEAD carries co-attribution
#   clean     the worktree has no uncommitted changes
set -uo pipefail

WT="${1:?usage: check-stage.sh <worktree> <base-sha> <report-file>}"
BASE="${2:?usage: check-stage.sh <worktree> <base-sha> <report-file>}"
REPORT="${3:?usage: check-stage.sh <worktree> <base-sha> <report-file>}"

name="$(basename "$REPORT" .md)"
stage="${name%%-*}"
failed=0
ok() { echo "ok    $1"; }
fail() { echo "FAIL  $1"; failed=1; }

# Report shape.
if [ ! -s "$REPORT" ]; then
  fail "report: $REPORT is missing or empty"
else
  missing=""
  for heading in "Status:" "### Commits" "### Files changed" "### Acceptance criteria" \
    "### Validations" "### Stage-specific" "### Concerns" "### Escalations"; do
    grep -q "^$heading" "$REPORT" || missing="$missing, $heading"
  done
  case "$stage" in
    architect) lines="Plan ID:|Retained:" ;;
    coder) lines="Deviations from plan:" ;;
    hardener) lines="Rules checked:|Claims checked:" ;;
    tester) lines="Coverage[^:]*:" ;;
    reviewer) lines="Verdict:" ;;
    *) lines="" ;;
  esac
  old_ifs="$IFS"; IFS='|'
  for line in $lines; do
    grep -q "^$line" "$REPORT" || missing="$missing, $line"
  done
  IFS="$old_ifs"
  [ -z "$missing" ] || fail "report: missing ${missing#, }"
  if grep -q '^Status: *BLOCKED' "$REPORT"; then
    fail "report: status BLOCKED"
  elif [ -z "$missing" ]; then
    ok "report: $(grep -m1 '^Status:' "$REPORT")"
  fi
fi

# Commits the report lists, against the branch.
range="$(git -C "$WT" rev-list "$BASE..HEAD" 2>/dev/null)" || {
  fail "commits: cannot list $BASE..HEAD in $WT"
  range=""
}
if [ -s "$REPORT" ]; then
  listed="$(awk '/^### Commits/{p=1; next} /^### /{p=0} p' "$REPORT" \
    | grep -oE '^`?[0-9a-f]{7,40}\b' | tr -d '`' || true)"
  absent=""
  for sha in $listed; do
    printf '%s\n' "$range" | grep -q "^$sha" || absent="$absent $sha"
  done
  if [ -n "$absent" ]; then
    fail "commits: not in $BASE..HEAD:$absent"
  else
    ok "commits: $(printf '%s' "$listed" | grep -c . || true) listed, all in the branch"
  fi
fi

# Co-attribution anywhere on the branch.
attrib="$(git -C "$WT" log --format='%h %B' "$BASE..HEAD" 2>/dev/null \
  | grep -iE 'co-authored-by|generated with' || true)"
if [ -n "$attrib" ]; then
  fail "attrib: $(printf '%s' "$attrib" | head -3 | tr '\n' ' ')"
else
  ok "attrib: none"
fi

# Clean tree.
dirty="$(git -C "$WT" status --porcelain 2>/dev/null)"
if [ -n "$dirty" ]; then
  fail "clean: $(printf '%s\n' "$dirty" | head -5 | tr '\n' ' ')"
else
  ok "clean: yes"
fi

exit "$failed"
