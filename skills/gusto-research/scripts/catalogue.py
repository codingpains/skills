#!/usr/bin/env python3
"""Sync the channel's videos and Shorts into $GUSTO_HOME/catalogue.jsonl and print a summary.

    python3 ~/.claude/skills/gusto-research/scripts/catalogue.py          # new videos, recent ones, and the stalest 40
    python3 ~/.claude/skills/gusto-research/scripts/catalogue.py --full   # every video (about 10 minutes)

One row per upload: id, kind (long|short), upload_date, views, likes, comments,
duration, title, synced (YYYY-MM-DD). Recent uploads are re-read every run
because their numbers still move; old ones are refreshed a few at a time.
"""
import argparse
import datetime as dt

from common import HOME, channel_url, iso_date, read_jsonl, short_number, watch_url, write_jsonl, yt_json_lines

CATALOGUE = HOME / "catalogue.jsonl"
RECENT_DAYS = 120
STALE_BATCH = 40
FIELDS = "%(.{id,upload_date,view_count,like_count,comment_count,duration,title})j"


def list_ids(kind):
    tab = "videos" if kind == "long" else "shorts"
    rows = yt_json_lines(["--flat-playlist", "--print", "%(.{id,title})j", f"{channel_url()}/{tab}"])
    return {row["id"]: kind for row in rows}


def pick_ids_to_fetch(listed, known, full):
    today = dt.date.today()
    if full:
        return list(listed)
    recent_cutoff = (today - dt.timedelta(days=RECENT_DAYS)).strftime("%Y%m%d")
    new = [vid for vid in listed if vid not in known]
    recent = [vid for vid in listed if vid in known and (known[vid].get("upload_date") or "") >= recent_cutoff]
    by_age = sorted((vid for vid in listed if vid in known and vid not in recent), key=lambda v: known[v].get("synced", ""))
    return new + recent + by_age[:STALE_BATCH]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--full", action="store_true", help="re-read every video")
    args = parser.parse_args()

    known = {row["id"]: row for row in read_jsonl(CATALOGUE)}
    listed = {**list_ids("long"), **list_ids("short")}
    if not listed:
        raise SystemExit(f"could not list {channel_url()}; check the URL in {HOME / 'channel.md'}")

    to_fetch = pick_ids_to_fetch(listed, known, args.full)
    today = dt.date.today().isoformat()
    for row in yt_json_lines(["--skip-download", "--ignore-no-formats-error", "--print", FIELDS,
                              *[watch_url(v) for v in to_fetch]]):
        known[row["id"]] = {
            "id": row["id"],
            "kind": listed.get(row["id"], "long"),
            "upload_date": row.get("upload_date"),
            "views": row.get("view_count"),
            "likes": row.get("like_count"),
            "comments": row.get("comment_count"),
            "duration": row.get("duration"),
            "title": row.get("title"),
            "synced": today,
        }

    removed = [vid for vid in known if vid not in listed]
    rows = sorted((known[v] for v in listed if v in known), key=lambda r: r.get("upload_date") or "", reverse=True)
    write_jsonl(CATALOGUE, rows)

    longs = [r for r in rows if r["kind"] == "long"]
    shorts = [r for r in rows if r["kind"] == "short"]
    print(f"catalogue: {len(longs)} long videos, {len(shorts)} Shorts -> {CATALOGUE}")
    print(f"read {len(to_fetch)} this run; {len(listed) - len(rows)} listed but unreadable; {len(removed)} gone from the channel")
    if rows:
        print(f"latest upload: {iso_date(rows[0]['upload_date'])} {rows[0]['title']}")
    print("\nlast 8 uploads:")
    for r in rows[:8]:
        print(f"  {iso_date(r['upload_date'])}  {short_number(r['views']):>6}  {r['kind']:<5}  {r['id']}  {r['title']}")


if __name__ == "__main__":
    main()
