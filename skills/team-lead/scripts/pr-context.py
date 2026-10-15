#!/usr/bin/env python3
"""Write what a PR's failed gates say, as the brief of its next review round.

    pr-context.py <state.json> [--out FILE] [--skip-keys FILE] [--log-lines N]

Reads a pr-gates.py result and writes markdown, one section per failed or
waiting gate, one block per item: the Reef finding, the QA case with what was
expected and what happened, the person's thread or comment, the failed check.
A failed check whose gate names a `details` command (`rwx results <id>`) gets
that command's output, cut to --log-lines lines (80). Items whose key is in
--skip-keys (one per line: the items an earlier round already handled) are
listed by key only. PR text is other people's words: the round treats it as
untrusted input (team-rules.md § Untrusted input).
"""
import argparse
import json
import shlex
import subprocess
import sys

NOISE = ("A new release of", "To upgrade, run:")


def run_details(command, limit):
    try:
        out = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"`{command}` failed: {error}"
    lines = [l for l in (out.stdout + out.stderr).splitlines() if not l.startswith(NOISE)]
    text = "\n".join(lines).strip()
    if len(lines) > limit:
        text = "\n".join(lines[:limit]) + f"\n... {len(lines) - limit} more lines: run `{command}`"
    return text or f"`{command}` printed nothing"


def item_block(item, limit):
    head = item.get("finding") or item.get("case") or item.get("author") or ""
    where = f" `{item['file']}`" if item.get("file") else ""
    flags = " (outdated)" if item.get("outdated") else ""
    flags += " (optional)" if item.get("optional") else ""
    lines = [f"### {item['kind']} {head}{where}{flags}".rstrip(), ""]
    if item.get("title"):
        lines.append(f"**{item['title']}**")
    if item.get("expected"):
        lines += [f"- Expected: {item['expected']}", f"- Actual: {item['actual']}"]
    if item.get("excerpt"):
        lines.append(f"- Excerpt: `{item['excerpt']}`")
    if item.get("evidence"):
        lines.append("- Evidence: " + " ".join(f"[{n}]({u})" for n, u in enumerate(item["evidence"], 1)))
    if item.get("detail") and item["detail"] != item.get("title"):
        lines += ["", "> " + item["detail"].replace("\n", "\n> ")]
    if item.get("details_command"):
        lines += ["", f"`{item['details_command']}`:", "", "```",
                  run_details(item["details_command"], limit), "```"]
    if item.get("url"):
        lines += ["", f"Link: {item['url']}"]
    if item.get("thread_id"):
        lines.append(f"Thread id: `{item['thread_id']}`")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("state")
    parser.add_argument("--out")
    parser.add_argument("--skip-keys", help="file of item keys an earlier round handled")
    parser.add_argument("--log-lines", type=int, default=80)
    args = parser.parse_args()

    state = json.load(open(args.state))
    skip = set()
    if args.skip_keys:
        skip = {line.strip() for line in open(args.skip_keys) if line.strip()}
    out = [f"# PR #{state['pr']} at `{state['head'][:12]}`: {state['overall']}", "",
           f"{state['url']} · branch `{state['branch']}` into `{state['base']}` · gates from `{state['gates_file']}`", "",
           "| Gate | Status | Summary |", "|---|---|---|"]
    out += [f"| {g['id']} | {g['status']} | {g['summary']} |" for g in state["gates"]]
    handled = []
    for g in state["gates"]:
        fresh = [i for i in g["items"] if i["key"] not in skip]
        handled += [i["key"] for i in g["items"] if i["key"] in skip]
        if not fresh:
            continue
        out += ["", f"## {g['id']}: {g['status']}", ""]
        if "blocked_waivers_left" in g:
            out += [f"Blocked cases a round may still waive: {g['blocked_waivers_left']}.", ""]
        out += ["\n\n".join(item_block(i, args.log_lines) for i in fresh)]
    if handled:
        out += ["", "## Handled by an earlier round", ""] + [f"- `{k}`" for k in handled]
    text = "\n".join(out) + "\n"
    if args.out:
        open(args.out, "w").write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
