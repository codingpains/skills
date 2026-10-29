#!/usr/bin/env python3
"""Collect the original images a storyboard is built from: video frames and images from web pages.

    python3 ~/.claude/skills/gusto-script/scripts/media.py frames 0RkvOeoZX78 --every 20 --out ~/.gusto-clasico/self/frames
    python3 ~/.claude/skills/gusto-script/scripts/media.py frames XJck0LcR9Ho --at 0:12 1:05 --out <production>/refs --name hook-2024
    python3 ~/.claude/skills/gusto-script/scripts/media.py page "https://www.gq.com/story/..."
    python3 ~/.claude/skills/gusto-script/scripts/media.py get "<image url>" --page "<article url>" --out <production>/refs --name 03-polo-azul --note "outfit 1"
    python3 ~/.claude/skills/gusto-script/scripts/media.py import <downloaded file> --image-url "<image url>" --page "<article url>" --out <production>/refs --name 03-polo-azul

frames  stills from a YouTube video (his own or any public one), saved as JPEG. Needs ffmpeg.
page    the images on an article or gallery page, largest first, with their alt text.
get     download one image and record where it came from in <out>/sources.json.
import  copy in an image a browser downloaded (for sites that block get), and record it the same way.

Every file saved is an original, kept for reference. sources.json says where each
one came from (page, image URL, date), so nothing is used without knowing its origin.
"""
import argparse
import datetime
import html.parser
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "gusto-research" / "scripts"))
from common import YT_ARGS, watch_url  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif", "image/gif": ".gif"}


def seconds(stamp):
    """'1:05', '01:02:03' or '65' as seconds."""
    total = 0.0
    for part in stamp.split(":"):
        total = total * 60 + float(part)
    return total


def clock(secs):
    secs = int(secs)
    return f"{secs // 60}m{secs % 60:02d}s"


def stream_url(video_id):
    """Direct URL of the video stream, at most 1080p, so ffmpeg can seek without downloading it all."""
    proc = subprocess.run(
        ["yt-dlp", *YT_ARGS, "-g", "-f", "bv*[height<=1080][ext=mp4]/bv*[height<=1080]/b", watch_url(video_id)],
        capture_output=True, text=True)
    urls = proc.stdout.split()
    if not urls:
        sys.exit(f"no stream for {video_id}: {proc.stderr.strip()[-500:]}")
    return urls[0], video_length(video_id)


def video_length(video_id):
    proc = subprocess.run(["yt-dlp", *YT_ARGS, "--print", "duration", watch_url(video_id)],
                          capture_output=True, text=True)
    try:
        return float(proc.stdout.split()[0])
    except (IndexError, ValueError):
        return None


def frames(args):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not installed: brew install ffmpeg")
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    url, length = stream_url(args.video)
    if args.at:
        stamps = [seconds(s) for s in args.at]
    else:
        if not length:
            sys.exit("could not read the video's length; pass --at instead of --every")
        stamps = [float(t) for t in range(int(args.every / 2), int(length), args.every)]
    prefix = args.name or args.video
    for at in stamps:
        path = out / f"{prefix}-{clock(at)}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(at), "-i", url,
                        "-frames:v", "1", "-q:v", "2", str(path)], check=False)
        if path.exists():
            record(out, path, {"video": args.video, "at": clock(at), "page": watch_url(args.video)})
            print(path)
        else:
            print(f"failed at {clock(at)}", file=sys.stderr)


class ImageFinder(html.parser.HTMLParser):
    """Collects og:image, twitter:image and every <img>/<source>, keeping the largest srcset entry."""

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.found = {}

    def add(self, url, alt="", width=0):
        if not url or url.startswith("data:"):
            return
        url = urllib.parse.urljoin(self.base, url.strip())
        if re.search(r"\.svg(\?|$)|logo|icon|sprite|avatar|pixel", url, re.I):
            return
        known = self.found.get(url)
        if not known or width > known["width"]:
            self.found[url] = {"url": url, "alt": alt or (known or {}).get("alt", ""), "width": width}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and (a.get("property") or a.get("name", "")) in ("og:image", "twitter:image"):
            self.add(a.get("content"), "(cover)", 99999)
        if tag in ("img", "source"):
            alt = a.get("alt", "")
            srcset = a.get("srcset") or a.get("data-srcset")
            if srcset:
                best = max(parse_srcset(srcset), key=lambda c: c[1], default=None)
                if best:
                    self.add(best[0], alt, best[1])
            self.add(a.get("src") or a.get("data-src"), alt, int(a.get("width") or 0) if str(a.get("width", "")).isdigit() else 0)


def parse_srcset(srcset):
    # Candidates are separated by a comma and whitespace; URLs may hold bare commas.
    for candidate in re.split(r",\s+", srcset):
        bits = candidate.strip().split()
        if not bits:
            continue
        width = 0
        if len(bits) > 1 and bits[1].endswith("w") and bits[1][:-1].isdigit():
            width = int(bits[1][:-1])
        yield bits[0], width


def fetch(url, referer=None):
    headers = {"User-Agent": UA, "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"}
    if referer:
        headers["Referer"] = referer
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30)


def page(args):
    with fetch(args.url) as resp:
        text = resp.read().decode(resp.headers.get_content_charset() or "utf-8", "replace")
    finder = ImageFinder(args.url)
    finder.feed(text)
    images = sorted(finder.found.values(), key=lambda i: -i["width"])
    images = [i for i in images if i["width"] == 0 or i["width"] >= args.min_width]
    if not images:
        print("no images found; the page may load them with JavaScript. Try the gallery's own URL or a frame.")
    for n, image in enumerate(images[: args.n], 1):
        width = "cover" if image["width"] == 99999 else (f"{image['width']}w" if image["width"] else "?w")
        print(f"{n:>2}. [{width}] {image['alt'][:90]}\n    {image['url']}")


def get(args):
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    with fetch(args.url, referer=args.page) as resp:
        kind = resp.headers.get_content_type()
        if not kind.startswith("image/"):
            sys.exit(f"not an image ({kind}): {args.url}")
        data = resp.read()
    path = out / (args.name + EXTENSIONS.get(kind, ".img"))
    path.write_bytes(data)
    record(out, path, {"image_url": args.url, "page": args.page, "note": args.note})
    print(path)


def sniff(data):
    """The image's extension from its first bytes; sites often label webp as jpeg and the reverse."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG"):
        return ".png"
    if data.startswith(b"GIF8"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[4:12] in (b"ftypavif", b"ftypavis"):
        return ".avif"
    return None


def import_file(args):
    source = Path(args.file).expanduser()
    data = source.read_bytes()
    extension = sniff(data[:16])
    if not extension:
        sys.exit(f"not an image: {source}")
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    path = out / (args.name + extension)
    shutil.copyfile(source, path)
    record(out, path, {"image_url": args.image_url, "page": args.page, "note": args.note, "via": "browser"})
    print(path)


def record(out, path, fields):
    """Append or replace the file's entry in sources.json."""
    sources_file = out / "sources.json"
    sources = json.loads(sources_file.read_text()) if sources_file.exists() else []
    sources = [s for s in sources if s.get("file") != path.name]
    entry = {"file": path.name, **{k: v for k, v in fields.items() if v}, "saved": datetime.date.today().isoformat()}
    sources.append(entry)
    sources_file.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("frames", help="stills from a YouTube video")
    p.add_argument("video", help="video ID (put IDs that start with '-' after '--')")
    p.add_argument("--out", required=True)
    p.add_argument("--at", nargs="+", help="timestamps, e.g. 0:12 1:05")
    p.add_argument("--every", type=int, default=20, help="seconds between stills when --at is not given")
    p.add_argument("--name", help="file name prefix (default: the video ID)")
    p.set_defaults(run=frames)

    p = sub.add_parser("page", help="list the images on a web page")
    p.add_argument("url")
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--min-width", type=int, default=500)
    p.set_defaults(run=page)

    p = sub.add_parser("get", help="download one image and record its source")
    p.add_argument("url")
    p.add_argument("--out", required=True)
    p.add_argument("--name", required=True, help="file name without extension, e.g. 03-polo-azul")
    p.add_argument("--page", help="the article or gallery the image is on")
    p.add_argument("--note", help="what it is a reference for")
    p.set_defaults(run=get)

    p = sub.add_parser("import", help="copy in an image a browser downloaded and record its source")
    p.add_argument("file", help="the downloaded file")
    p.add_argument("--image-url", required=True, help="the image's own URL")
    p.add_argument("--page", required=True, help="the article or product page it is on")
    p.add_argument("--out", required=True)
    p.add_argument("--name", required=True, help="file name without extension, e.g. 03-polo-azul")
    p.add_argument("--note", help="what it is a reference for")
    p.set_defaults(run=import_file)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
