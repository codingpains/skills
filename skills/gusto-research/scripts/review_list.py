#!/usr/bin/env python3
"""Write or refresh $GUSTO_HOME/catalogue-review.md, where Gustavo marks which old videos he still stands by.

    python3 ~/.claude/skills/gusto-research/scripts/review_list.py            # top 80 by views + everything since 2022
    python3 ~/.claude/skills/gusto-research/scripts/review_list.py --top 150
    python3 ~/.claude/skills/gusto-research/scripts/review_list.py --show     # print the marks, no rewrite

Marks: [k] keep (safe to link and to send viewers to), [o] outdated (never
link), [r] remake (redo it as a new video), [ ] not reviewed. Text after
" // " is his note. Marks and notes survive a refresh.
"""
import argparse
import re

from common import HOME, iso_date, read_jsonl, short_number

REVIEW = HOME / "catalogue-review.md"
LINE = re.compile(r"^- \[(.)\] (\S+) · .*?(?: // (.*))?$")
HEADER = """# Back catalogue review

Mark each video, then save. Only `[k]` videos are linked from new videos or used
as the end-of-video "watch this next".

- `[k]` keep: I still stand by it
- `[o]` outdated: never link it
- `[r]` remake: worth redoing as a new video
- `[ ]` not reviewed yet

Add a note after ` // ` if useful, e.g. `// the advice holds, the outfits look dated`.

"""


def read_marks():
    marks = {}
    if REVIEW.exists():
        for line in REVIEW.read_text().splitlines():
            match = LINE.match(line)
            if match:
                marks[match.group(2)] = (match.group(1), match.group(3))
    return marks


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--top", type=int, default=80)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    marks = read_marks()
    if args.show:
        for mark in ["k", "r", "o", " "]:
            ids = [vid for vid, (m, _) in marks.items() if m == mark]
            print(f"[{mark}] {len(ids)}: {' '.join(ids)}")
        return

    longs = [r for r in read_jsonl(HOME / "catalogue.jsonl") if r["kind"] == "long"]
    if not longs:
        raise SystemExit("no catalogue yet; run catalogue.py first")
    by_views = sorted(longs, key=lambda r: r.get("views") or 0, reverse=True)
    keep = {r["id"] for r in by_views[: args.top]}
    keep |= {r["id"] for r in longs if (r.get("upload_date") or "") >= "20220101"}
    keep |= set(marks)

    lines = []
    for r in by_views:
        if r["id"] not in keep:
            continue
        mark, note = marks.get(r["id"], (" ", None))
        line = f"- [{mark}] {r['id']} · {iso_date(r.get('upload_date'))} · {short_number(r.get('views'))} · {r.get('title')}"
        lines.append(line + (f" // {note}" if note else ""))
    REVIEW.write_text(HEADER + "\n".join(lines) + "\n")
    reviewed = sum(1 for m, _ in marks.values() if m != " ")
    print(f"{len(lines)} videos in {REVIEW}; {reviewed} already marked")


if __name__ == "__main__":
    main()
