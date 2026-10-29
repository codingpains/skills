#!/usr/bin/env python3
"""Save the Spanish transcript of one or more videos as plain text and print its path.

    python3 ~/.claude/skills/gusto-research/scripts/transcript.py XJck0LcR9Ho -- -7KeuEJ0bBU

Transcripts are cached in $GUSTO_HOME/transcripts/<id>.txt. Works for any public
video, the channel's own or another channel's. Put IDs that start with '-' after '--'.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from common import HOME, YT_ARGS, watch_url

TRANSCRIPTS = HOME / "transcripts"


def json3_to_text(path):
    events = json.loads(path.read_text()).get("events", [])
    words = ("".join(seg.get("utf8", "") for seg in event.get("segs", [])) for event in events)
    return " ".join(" ".join(words).split())


def fetch(video_id):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["yt-dlp", *YT_ARGS, "--skip-download", "--write-subs", "--write-auto-subs",
                        "--sub-langs", "es-orig,es,es-MX,es-419,en", "--sub-format", "json3",
                        "-o", f"{tmp}/%(id)s.%(ext)s", watch_url(video_id)], capture_output=True, text=True)
        found = sorted(Path(tmp).glob("*.json3"))
        # Prefer a Spanish track over the English fallback.
        found.sort(key=lambda p: ".en." in p.name)
        return json3_to_text(found[0]) if found else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="+")
    args = parser.parse_args()
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    for video_id in args.ids:
        out = TRANSCRIPTS / f"{video_id}.txt"
        if not out.exists():
            text = fetch(video_id)
            if not text:
                print(f"{video_id}: no transcript")
                continue
            out.write_text(text)
        print(f"{video_id}: {out} ({len(out.read_text().split())} words)")


if __name__ == "__main__":
    main()
