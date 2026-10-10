#!/usr/bin/env python3
"""The repo rule files that apply to a set of touched files, so the Lead can
list them once in handoff-common.md instead of every stage finding them.

    list-rules.py <worktree> [--base <sha>] [<repo-relative file> ...]

The touched files are the ones named, plus `git diff --name-only <base>..HEAD`
with --base. Prints one absolute path per line, as team-rules § Repo rules
orders them:

1. every CLAUDE.md and AGENTS.md from the repo root down to each touched
   file's folder;
2. every rule file under a .claude/rules/ folder that sits at the root or in
   a folder above a touched file, when its frontmatter `paths` or `globs`
   match a touched file (relative to the folder holding .claude/), or when
   it has no such filter.

Exits 1 with a message when it cannot list the files.
"""
import os
import re
import subprocess
import sys


def glob_regex(pattern):
    """A gitignore-style glob (**, *, ?, {a,b}, [..]) as an anchored regex."""
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "{":
            end = pattern.find("}", i)
            if end < 0:
                out.append(re.escape(c))
            else:
                alts = pattern[i + 1:end].split(",")
                out.append("(?:" + "|".join(glob_regex(a)[1:-1] for a in alts) + ")")
                i = end
        elif c == "[":
            end = pattern.find("]", i)
            if end < 0:
                out.append(re.escape(c))
            else:
                out.append(pattern[i:end + 1])
                i = end
        else:
            out.append(re.escape(c))
        i += 1
    return "^" + "".join(out) + "$"


def frontmatter_globs(path):
    """The `paths`/`globs` patterns in a rule file's frontmatter; [] means none."""
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return []
    if not lines or lines[0].strip() != "---":
        return []
    globs, key = [], None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^(paths|globs)\s*:\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value:
                value = value.strip("[]")
                globs += [v.strip().strip("'\"") for v in value.split(",") if v.strip()]
                key = None
            continue
        if key and re.match(r"^\s*-\s*", line):
            globs.append(re.sub(r"^\s*-\s*", "", line).strip().strip("'\""))
        elif not line.startswith((" ", "\t")):
            key = None
    return [g for g in globs if g]


def git(worktree, *args):
    return subprocess.run(["git", "-C", worktree, *args], capture_output=True, text=True, check=True).stdout


def main(argv):
    if not argv or argv[0].startswith("-"):
        sys.exit(__doc__)
    worktree, rest = os.path.abspath(argv[0]), argv[1:]
    touched = []
    while rest:
        if rest[0] == "--base" and len(rest) > 1:
            try:
                touched += git(worktree, "diff", "--name-only", f"{rest[1]}..HEAD").split()
            except subprocess.CalledProcessError as e:
                sys.exit(f"list-rules: git diff failed: {e.stderr.strip()}")
            rest = rest[2:]
        else:
            touched.append(rest[0].lstrip("./"))
            rest = rest[1:]
    touched = sorted(set(touched))
    if not touched:
        sys.exit("list-rules: no touched files")

    # Folders from the root down to each touched file's folder: "" is the root.
    folders = {""}
    for f in touched:
        parts = f.split("/")[:-1]
        folders.update("/".join(parts[:n]) for n in range(1, len(parts) + 1))
    folders = sorted(folders, key=lambda d: (d.count("/") + (d != ""), d))

    found = []
    for d in folders:
        for name in ("CLAUDE.md", "AGENTS.md"):
            p = os.path.join(worktree, d, name)
            if os.path.isfile(p):
                found.append(p)
    for d in folders:
        rules_dir = os.path.join(worktree, d, ".claude", "rules")
        if not os.path.isdir(rules_dir):
            continue
        prefix = d + "/" if d else ""
        below = [f[len(prefix):] for f in touched if f.startswith(prefix)]
        for root, _, files in os.walk(rules_dir):
            for name in sorted(files):
                if not name.endswith((".md", ".mdc")):
                    continue
                p = os.path.join(root, name)
                globs = frontmatter_globs(p)
                if not globs or any(re.match(glob_regex(g), f) for g in globs for f in below):
                    found.append(p)
    print("\n".join(found))


if __name__ == "__main__":
    main(sys.argv[1:])
