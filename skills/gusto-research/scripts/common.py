"""Shared helpers for the gusto-research scripts: the private home folder and yt-dlp calls."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path(os.environ.get("GUSTO_HOME", Path.home() / ".gusto-clasico"))
DEFAULT_CHANNEL = "https://www.youtube.com/@GustoClasicoOficial"
# Spanish titles, not YouTube's auto-translation into the machine's language.
YT_ARGS = ["--extractor-args", "youtube:lang=es", "--ignore-errors", "--no-warnings"]


def channel_url():
    """The channel URL from channel.md's `channel:` line, else the default."""
    profile = HOME / "channel.md"
    if profile.exists():
        match = re.search(r"^channel:\s*(\S+)", profile.read_text(), re.M)
        if match:
            return match.group(1).rstrip("/")
    return DEFAULT_CHANNEL


def watch_url(video_id):
    # A bare ID that starts with '-' would be read as a yt-dlp option.
    return "https://www.youtube.com/watch?v=" + video_id


def yt_json_lines(args):
    """Run yt-dlp with a JSON --print template and return one dict per printed line."""
    try:
        proc = subprocess.run(["yt-dlp", *YT_ARGS, *args], capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("yt-dlp is not installed: brew install yt-dlp")
    rows = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not rows and proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
    return rows


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def short_number(n):
    if n is None:
        return "?"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def iso_date(yyyymmdd):
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}" if yyyymmdd else "?"
