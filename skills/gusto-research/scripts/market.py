#!/usr/bin/env python3
"""Read the market: what people search for, what ranks, and what other channels publish.

    python3 ~/.claude/skills/gusto-research/scripts/market.py suggest "como vestir" "rutina gimnasio" [--expand]
    python3 ~/.claude/skills/gusto-research/scripts/market.py search "cómo vestir casual elegante" [--n 15]
    python3 ~/.claude/skills/gusto-research/scripts/market.py channel @JoseZunigaEspanol [--n 20]

suggest  YouTube autocomplete (Mexico, Spanish). --expand adds "<query> a".."<query> z".
search   the top results for a query: views, length, channel. High views on old
         videos from small channels mean demand nobody serves well.
channel  a channel's latest uploads with views, newest first.
"""
import argparse
import json
import string
import urllib.parse
import urllib.request

from common import short_number, yt_json_lines

SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=es&gl=MX&q="


def suggest(queries, expand):
    seen = []
    for query in queries:
        variants = [query] + ([f"{query} {letter}" for letter in string.ascii_lowercase] if expand else [])
        for variant in variants:
            with urllib.request.urlopen(SUGGEST_URL + urllib.parse.quote(variant), timeout=10) as resp:
                suggestions = json.loads(resp.read().decode("utf-8", "replace"))[1]
            for s in suggestions:
                if s not in seen:
                    seen.append(s)
                    print(s)


def print_videos(rows):
    for r in rows:
        minutes = f"{(r.get('duration') or 0) // 60}m"
        channel = r.get("channel") or ""
        print(f"{short_number(r.get('view_count')):>6}  {minutes:>4}  {r['id']}  {channel[:24]:<24}  {r.get('title')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_suggest = sub.add_parser("suggest")
    p_suggest.add_argument("queries", nargs="+")
    p_suggest.add_argument("--expand", action="store_true")
    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--n", type=int, default=15)
    p_channel = sub.add_parser("channel")
    p_channel.add_argument("handle", help="@handle or channel URL")
    p_channel.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    fields = "%(.{id,title,view_count,duration,channel})j"
    if args.command == "suggest":
        suggest(args.queries, args.expand)
    elif args.command == "search":
        print_videos(yt_json_lines(["--flat-playlist", "--print", fields, f"ytsearch{args.n}:{args.query}"]))
    else:
        url = args.handle if args.handle.startswith("http") else f"https://www.youtube.com/{args.handle}"
        print_videos(yt_json_lines(["--flat-playlist", "-I", f"1:{args.n}", "--print", fields, f"{url}/videos"]))


if __name__ == "__main__":
    main()
