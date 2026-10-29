#!/usr/bin/env python3
"""Fetch comments on recent videos and list what the audience asks for.

    python3 ~/.claude/skills/gusto-research/scripts/comments.py               # sync the 10 latest long videos, then digest
    python3 ~/.claude/skills/gusto-research/scripts/comments.py --recent 25
    python3 ~/.claude/skills/gusto-research/scripts/comments.py --ids XJck0LcR9Ho P_WG0WQGoUM
    python3 ~/.claude/skills/gusto-research/scripts/comments.py --no-sync     # digest what is saved

Comments are saved to $GUSTO_HOME/comments/<id>.json. The digest goes to stdout
and $GUSTO_HOME/audience.md: regulars (people who comment on several videos),
then requests and questions, regulars first, then by likes.
"""
import argparse
import datetime as dt
import json
import unicodedata

from common import HOME, iso_date, read_jsonl, watch_url, yt_json_lines

COMMENTS = HOME / "comments"
DIGEST = HOME / "audience.md"
# Phrases that turn a comment into a topic request, compared without accents.
REQUEST_MARKERS = [
    "video de", "video sobre", "un video", "podrias", "puedes hacer", "haz un", "hagas", "me gustaria",
    "recomiendas", "recomiendan", "que opinas", "como combin", "como vestir", "como usar", "consejo",
    "hablar de", "hables", "hablaras", "abordaras", "tema de", "ojala", "estaria bueno", "segunda parte",
    "parte 2", "continuacion",
]


def plain(text):
    folded = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in folded if not unicodedata.combining(c))


def sync(video_ids):
    COMMENTS.mkdir(parents=True, exist_ok=True)
    rows = yt_json_lines([
        "--skip-download", "--ignore-no-formats-error", "--write-comments", "--no-write-info-json",
        "--extractor-args", "youtube:max_comments=400,all,100,10;comment_sort=top",
        "--print", "%(.{id,title,comments})j", *[watch_url(v) for v in video_ids],
    ])
    for row in rows:
        payload = {"id": row["id"], "title": row.get("title"), "fetched": dt.date.today().isoformat(),
                   "comments": row.get("comments") or []}
        (COMMENTS / f"{row['id']}.json").write_text(json.dumps(payload, ensure_ascii=False))
    print(f"saved comments for {len(rows)} of {len(video_ids)} videos")


def is_request(text):
    t = plain(text)
    return "?" in text or any(marker in t for marker in REQUEST_MARKERS)


def digest():
    files = sorted(COMMENTS.glob("*.json"))
    if not files:
        raise SystemExit("no comments saved yet; run without --no-sync")
    videos = [json.loads(f.read_text()) for f in files]

    seen_on = {}  # author_id -> set of video ids
    names = {}
    for video in videos:
        for c in video["comments"]:
            if c.get("author_is_uploader"):
                continue
            author = c.get("author_id") or c.get("author")
            seen_on.setdefault(author, set()).add(video["id"])
            names[author] = c.get("author")
    regulars = {a for a, vids in seen_on.items() if len(vids) >= 2}

    asks = []
    for video in videos:
        for c in video["comments"]:
            if c.get("author_is_uploader") or c.get("parent", "root") != "root":
                continue
            if is_request(c.get("text", "")):
                author = c.get("author_id") or c.get("author")
                asks.append((author in regulars, c.get("like_count") or 0, video, c))
    asks.sort(key=lambda a: (a[0], a[1]), reverse=True)

    lines = [f"# Audience digest ({dt.date.today().isoformat()})", "",
             f"{len(videos)} videos, {sum(len(v['comments']) for v in videos)} comments, {len(regulars)} regulars.", "",
             "## Regulars (commented on 2+ videos)", ""]
    for author in sorted(regulars, key=lambda a: -len(seen_on[a]))[:40]:
        lines.append(f"- {names[author]} — {len(seen_on[author])} videos")
    lines += ["", "## Requests and questions", ""]
    for regular, likes, video, c in asks[:120]:
        text = " ".join(c.get("text", "").split())[:300]
        tag = "regular" if regular else "viewer"
        lines.append(f"- [{tag}, {likes} likes] {c.get('author')} on {video['id']} ({video.get('title')}): {text}")
    DIGEST.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recent", type=int, default=10, help="latest long videos to sync (default 10)")
    parser.add_argument("--ids", nargs="*", default=[], help="extra video IDs to sync")
    parser.add_argument("--no-sync", action="store_true", help="only rebuild the digest")
    args = parser.parse_args()

    if not args.no_sync:
        catalogue = read_jsonl(HOME / "catalogue.jsonl")
        if not catalogue and not args.ids:
            raise SystemExit("no catalogue yet; run catalogue.py first")
        recent = [r["id"] for r in catalogue if r["kind"] == "long"][: args.recent]
        sync(list(dict.fromkeys(recent + args.ids)))
        if catalogue:
            print(f"latest synced upload: {iso_date(catalogue[0]['upload_date'])}")
    digest()


if __name__ == "__main__":
    main()
