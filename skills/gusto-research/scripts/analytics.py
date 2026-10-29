#!/usr/bin/env python3
"""Read the channel's private YouTube Analytics (owner only).

    python3 ~/.claude/skills/gusto-research/scripts/analytics.py auth              # once: sign in in the browser
    python3 ~/.claude/skills/gusto-research/scripts/analytics.py channel --days 90
    python3 ~/.claude/skills/gusto-research/scripts/analytics.py video XJck0LcR9Ho --days 28

channel  top videos in the window (views, average % watched, subscribers gained),
         subscriber vs non-subscriber views, traffic sources, YouTube search terms, countries.
video    one video over its first N days: the same, plus where its viewers came from.

Setup: a Google Cloud project with the "YouTube Analytics API" and "YouTube Data
API v3" enabled, and an OAuth client of type "Desktop app". Its JSON goes to
$GUSTO_HOME/secrets/client_secret.json. Tokens are kept next to it (mode 600).
Raw responses are saved to $GUSTO_HOME/analytics/. Impressions and click-through
rate are not in this API: export them from YouTube Studio into
$GUSTO_HOME/analytics/studio/ instead.
"""
import argparse
import datetime as dt
import http.server
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

from common import HOME, read_jsonl

SECRETS = HOME / "secrets"
CLIENT = SECRETS / "client_secret.json"
TOKEN = SECRETS / "token.json"
OUT = HOME / "analytics"
SCOPES = "https://www.googleapis.com/auth/yt-analytics.readonly https://www.googleapis.com/auth/youtube.readonly"
REPORTS = "https://youtubeanalytics.googleapis.com/v2/reports"
TOKEN_URL = "https://oauth2.googleapis.com/token"
# YouTube Analytics data lags by about two days.
LAG_DAYS = 2


def client():
    if not CLIENT.exists():
        sys.exit(f"missing {CLIENT}: create a Desktop OAuth client in Google Cloud and save its JSON there")
    data = json.loads(CLIENT.read_text())
    return data.get("installed") or data.get("web")


def post_form(url, fields):
    body = urllib.parse.urlencode(fields).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=30) as resp:
        return json.loads(resp.read())


def save_token(token):
    SECRETS.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(json.dumps(token))
    os.chmod(TOKEN, 0o600)


def auth():
    c = client()
    state = secrets.token_urlsafe(16)
    received = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            received.update({k: v[0] for k, v in query.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Listo. Ya puedes cerrar esta pestaña.".encode())

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent", "state": state,
    })
    print("Opening the browser. Sign in with the account that owns the channel.\nIf it does not open:", url)
    webbrowser.open(url)
    while "code" not in received and "error" not in received:
        server.handle_request()
    if received.get("state") != state or "code" not in received:
        sys.exit(f"sign-in failed: {received.get('error', 'state mismatch')}")
    token = post_form(TOKEN_URL, {
        "code": received["code"], "client_id": c["client_id"], "client_secret": c["client_secret"],
        "redirect_uri": redirect, "grant_type": "authorization_code",
    })
    token["expires_at"] = time.time() + token.get("expires_in", 3600) - 60
    save_token(token)
    print(f"signed in; token saved to {TOKEN}")


def access_token():
    client()
    if not TOKEN.exists():
        sys.exit("not signed in: run `analytics.py auth` first")
    token = json.loads(TOKEN.read_text())
    if time.time() < token.get("expires_at", 0):
        return token["access_token"]
    c = client()
    try:
        fresh = post_form(TOKEN_URL, {
            "client_id": c["client_id"], "client_secret": c["client_secret"],
            "refresh_token": token["refresh_token"], "grant_type": "refresh_token",
        })
    except urllib.error.HTTPError as err:
        # An OAuth app left in "Testing" loses its refresh token after 7 days.
        sys.exit(f"token refresh failed ({err.code}); run `analytics.py auth` again")
    token.update(access_token=fresh["access_token"], expires_at=time.time() + fresh.get("expires_in", 3600) - 60)
    save_token(token)
    return token["access_token"]


def query(start, end, metrics, **params):
    """One Analytics report as a list of dicts keyed by column name."""
    fields = {"ids": "channel==MINE", "startDate": start, "endDate": end, "metrics": metrics, **params}
    request = urllib.request.Request(REPORTS + "?" + urllib.parse.urlencode(fields),
                                     headers={"Authorization": "Bearer " + access_token()})
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return [{"error": f"{err.code}: {err.read().decode()[:300]}"}]
    names = [h["name"] for h in data.get("columnHeaders", [])]
    return [dict(zip(names, row)) for row in data.get("rows", [])]


def window(days, start=None):
    latest = dt.date.today() - dt.timedelta(days=LAG_DAYS)
    if start:
        end = min(start + dt.timedelta(days=days - 1), latest)
    else:
        end, start = latest, latest - dt.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def breakdowns(start, end, video_filter=None):
    extra = {"filters": video_filter} if video_filter else {}
    search_filter = "insightTrafficSourceType==YT_SEARCH" + (";" + video_filter if video_filter else "")
    return {
        "subscribed_status": query(start, end, "views,averageViewPercentage", dimensions="subscribedStatus", **extra),
        "traffic_sources": query(start, end, "views", dimensions="insightTrafficSourceType", sort="-views", **extra),
        "search_terms": query(start, end, "views", dimensions="insightTrafficSourceDetail",
                              filters=search_filter, sort="-views", maxResults=25),
        "countries": query(start, end, "views", dimensions="country", sort="-views", maxResults=10, **extra),
    }


def print_report(title, report, titles):
    print(f"# {title}\n")
    for section, rows in report.items():
        print(f"## {section}")
        for row in rows:
            if "video" in row:
                row = {"title": titles.get(row["video"], ""), **row}
            print("  " + "  ".join(f"{k}={v}" for k, v in row.items()))
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth")
    p_channel = sub.add_parser("channel")
    p_channel.add_argument("--days", type=int, default=90)
    p_video = sub.add_parser("video")
    p_video.add_argument("id")
    p_video.add_argument("--days", type=int, default=28)
    args = parser.parse_args()

    if args.command == "auth":
        auth()
        return

    catalogue = {r["id"]: r for r in read_jsonl(HOME / "catalogue.jsonl")}
    titles = {vid: r.get("title", "") for vid, r in catalogue.items()}
    per_video = "views,averageViewPercentage,averageViewDuration,subscribersGained,likes,comments,shares"
    if args.command == "channel":
        start, end = window(args.days)
        report = {"top_videos": query(start, end, per_video, dimensions="video", sort="-views", maxResults=50),
                  **breakdowns(start, end)}
        name = f"channel-{end}-{args.days}d"
    else:
        uploaded = (catalogue.get(args.id) or {}).get("upload_date")
        if not uploaded:
            sys.exit(f"{args.id} is not in the catalogue; run catalogue.py first")
        start, end = window(args.days, dt.datetime.strptime(uploaded, "%Y%m%d").date())
        report = {"totals": query(start, end, per_video, filters=f"video=={args.id}"),
                  **breakdowns(start, end, f"video=={args.id}")}
        name = f"video-{args.id}-{args.days}d"

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps({"start": start, "end": end, **report}, ensure_ascii=False, indent=1))
    print_report(f"{name} ({start} to {end})", report, titles)


if __name__ == "__main__":
    main()
