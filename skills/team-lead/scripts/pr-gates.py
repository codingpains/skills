#!/usr/bin/env python3
"""Read where an open PR stands against its repo's merge gates.

    pr-gates.py <PR URL | number> [--repo owner/repo] [--gates FILE] [--me LOGIN]
                [--summary]
    pr-gates.py --show <saved result>    the --summary of a saved result

Reads the PR, its reviews, comments, review threads, check runs and commit
statuses with `gh`, scores each gate in the repo's gates file on the PR's
latest commit, and prints one JSON object:

    {"pr", "url", "state", "head", "head_age_minutes", "mergeable",
     "auto_merge", "overall", "waiting_on", "gates": [{"id", "kind",
     "status", "summary", "items": [...]}], "gates_file", "signature"}

A gate's status is `running` (a bot or check is working on it), `waiting`
(nothing is working on it: a person has not reviewed, or a bot was not
asked), `pass` or `fail`. Items are what a review round would address, each
with a stable `key` so the watcher can tell new items from handled ones.

`overall`, first match wins: `merged`, `closed`, `conflict`, `running`
(some gate is running), `ready` (every gate passes), `round-needed` (every
gate has finished and one failed), `stalled` (some gate is waiting and none
is running; `waiting_on` names them).

The gates file is `~/.team-lead/repos/<name>.gates.json` whose `remote` matches the PR's
repo (repo-profiles.md § PR gates). Without one: every check on the head
commit, and one human approval. Reads only; never writes to GitHub.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

REPOS = os.path.expanduser("~/.team-lead/repos")

DEFAULT_GATES = {
    "gates": [
        {"id": "ci", "kind": "checks", "required": "all"},
        {"id": "human", "kind": "human", "min_approvals": 1},
    ]
}
START_GRACE_MINUTES = 15
DETAIL_LIMIT = 4000
PASS = {"success", "neutral", "skipped"}
FAIL = {"failure", "timed_out", "cancelled", "action_required", "error", "startup_failure", "stale"}
THREADS_QUERY = """query($owner:String!,$repo:String!,$n:Int!,$after:String){
 repository(owner:$owner,name:$repo){pullRequest(number:$n){
  reviewThreads(first:100,after:$after){pageInfo{hasNextPage endCursor}
   nodes{id isResolved isOutdated path line
    comments(first:50){nodes{author{login __typename} body url createdAt}}}}}}}"""


def gh(*args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"pr-gates: gh {' '.join(args[:3])} failed: {out.stderr.strip()}")
    return json.loads(out.stdout) if out.stdout.strip() else None


def gh_pages(path):
    """Every item of a paginated REST list."""
    pages = gh("api", "--paginate", "--slurp", path)
    items = []
    for page in pages or []:
        items.extend(page if isinstance(page, list) else page.get("check_runs", []))
    return items


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def matches(login, patterns):
    return any(fnmatch.fnmatch(login or "", p) for p in patterns or [])


def find_gates(remote, explicit):
    if explicit:
        return explicit, json.load(open(explicit))
    for path in sorted(glob.glob(os.path.join(REPOS, "*.gates.json"))):
        data = json.load(open(path))
        if data.get("remote") == remote:
            return path, data
    return None, DEFAULT_GATES


class PR:
    """Everything the gates read, fetched once."""

    def __init__(self, repo, number, me):
        self.repo, self.number = repo, number
        owner, name = repo.split("/")
        view = gh("pr", "view", str(number), "-R", repo, "--json",
                  "number,url,state,isDraft,headRefOid,headRefName,baseRefName,"
                  "mergeable,labels,author,autoMergeRequest")
        self.view = view
        self.head = view["headRefOid"]
        self.author = (view.get("author") or {}).get("login")
        self.me = me or gh("api", "user").get("login")
        self.labels = {label["name"] for label in view.get("labels", [])}
        commit = gh("api", f"repos/{repo}/commits/{self.head}")
        self.head_time = parse_time(commit["commit"]["committer"]["date"])
        self.head_age = (datetime.now(timezone.utc) - self.head_time).total_seconds() / 60
        self.comments = gh_pages(f"repos/{repo}/issues/{number}/comments?per_page=100")
        self.reviews = gh_pages(f"repos/{repo}/pulls/{number}/reviews?per_page=100")
        runs = gh_pages(f"repos/{repo}/commits/{self.head}/check-runs?per_page=100")
        self.check_runs = {}
        for run in sorted(runs, key=lambda r: r["id"]):
            self.check_runs[run["name"]] = run  # the latest run of each name wins
        status = gh("api", f"repos/{repo}/commits/{self.head}/status?per_page=100")
        self.statuses = {s["context"]: s for s in status.get("statuses", [])}
        self.threads = []
        after = None
        while True:
            args = ["api", "graphql", "-F", f"owner={owner}", "-F", f"repo={name}",
                    "-F", f"n={number}", "-f", f"query={THREADS_QUERY}"]
            if after:
                args += ["-f", f"after={after}"]
            page = gh(*args)["data"]["repository"]["pullRequest"]["reviewThreads"]
            self.threads.extend(page["nodes"])
            if not page["pageInfo"]["hasNextPage"]:
                break
            after = page["pageInfo"]["endCursor"]

    def ours(self, login):
        """The PR's author or the person running the watcher: their comments answer, never ask."""
        return login in (self.me, self.author)

    def comments_by(self, patterns):
        return [c for c in self.comments if matches(c["user"]["login"], patterns)]

    def unanswered_threads(self):
        """Unresolved threads whose last word is not ours."""
        for thread in self.threads:
            notes = thread["comments"]["nodes"]
            if thread["isResolved"] or not notes:
                continue
            last = (notes[-1].get("author") or {}).get("login")
            if self.ours(last):
                continue
            first = notes[0]
            yield thread, (first.get("author") or {}), first


def gate(spec, status, summary, items=()):
    return {"id": spec["id"], "kind": spec["kind"], "status": status,
            "summary": summary, "items": list(items)}


def not_started(pr, spec, what):
    """A gate with nothing on the head commit: still starting, or never asked."""
    grace = spec.get("start_grace_minutes", START_GRACE_MINUTES)
    if pr.head_age < grace:
        return gate(spec, "running", f"{what}: nothing on this commit yet, it is {pr.head_age:.0f} min old")
    return gate(spec, "waiting", f"{what}: nothing on this commit")


def check_state(pr, name):
    """(state, conclusion or description, url) of a check run or commit status, or None."""
    run = pr.check_runs.get(name)
    if run:
        if run["status"] != "completed":
            return "running", run["status"], run["html_url"]
        conclusion = run["conclusion"] or ""
        state = "pass" if conclusion in PASS else "fail" if conclusion in FAIL else "running"
        return state, conclusion, run["html_url"]
    status = pr.statuses.get(name)
    if status:
        state = {"success": "pass", "pending": "running"}.get(status["state"], "fail")
        return state, status.get("description") or status["state"], status.get("target_url")
    return None


def thread_item(thread, author, first, kind):
    body = first["body"].strip()
    return {"key": f"thread:{thread['id']}", "kind": kind, "thread_id": thread["id"],
            "file": f"{thread['path']}:{thread['line']}" if thread.get("path") else None,
            "outdated": thread["isOutdated"], "author": author.get("login"),
            "title": body.splitlines()[0][:200] if body else "", "url": first["url"],
            "detail": "\n\n".join(f"{(c.get('author') or {}).get('login')}: {c['body'].strip()}"
                                  for c in thread["comments"]["nodes"])[:DETAIL_LIMIT]}


def threads_for(pr, spec, kind):
    return [thread_item(t, a, f, kind) for t, a, f in pr.unanswered_threads()
            if matches(a.get("login"), spec.get("authors"))]


# ---- gate kinds -----------------------------------------------------------

def checks_gate(pr, spec):
    required = spec.get("required", "all")
    names = sorted(set(pr.check_runs) | set(pr.statuses)) if required == "all" else required
    if not names:
        return not_started(pr, spec, "checks")
    details = spec.get("details") or {}
    states, items = {}, []
    for name in names:
        found = check_state(pr, name)
        if not found:
            states[name] = "missing"
            continue
        state, note, url = found
        states[name] = state
        if state == "fail":
            item = {"key": f"ci:{name}@{pr.head[:12]}", "kind": "ci", "title": f"{name}: {note}", "url": url}
            match = re.search(details.get("url_pattern", "$^"), url or "")
            if match:
                item["details_command"] = details["command"].format(id=match.group(1))
                if details.get("retry"):
                    item["retry_command"] = details["retry"].format(id=match.group(1))
            items.append(item)
    summary = ", ".join(f"{n} {s}" for n, s in states.items())
    if any(s == "running" for s in states.values()):
        return gate(spec, "running", summary, items)
    if "missing" in states.values():
        started = not_started(pr, spec, "checks")
        if started["status"] == "running" or not items:
            return dict(started, summary=summary, items=items)
    return gate(spec, "fail" if items else "pass", summary, items)


REEF_MARKER = re.compile(r"<!-- (reef-[a-z-]+)(?::\s*([^>]*?))?\s*-->")
REEF_FINDING = re.compile(r"^- \S+ \*\*(F\d+)\*\*\s*(?:[^`\s]+\s+)?(?:`([^`]+)`)?:?\s*(.*)$")


def parse_reef(body):
    marks = {}
    for key, value in REEF_MARKER.findall(body):
        marks.setdefault(key, value.strip())
    conclusion, _, risk = marks.get("reef-conclusion", "").partition("; risk:")
    findings, section = [], None
    verdict = body.split("<!-- reef-status:end -->", 1)[-1].split("<!-- reef-approval-anchor -->", 1)[0]
    for line in verdict.splitlines():
        heading = re.match(r"^(?:### |<summary>)(.*?)(?:</summary>)?$", line.strip())
        if heading:  # "### To fix", or a fold such as "<summary>2 optional findings</summary>"
            section = heading.group(1).strip()
            continue
        match = REEF_FINDING.match(line.strip())
        if match:
            findings.append({"id": match.group(1), "file": match.group(2),
                             "text": match.group(3), "section": section})
    return {"conclusion": conclusion.strip(), "risk": risk.strip(), "head": marks.get("reef-head-sha"),
            "merge": marks.get("reef-merge"), "findings": findings}


def reef_gate(pr, spec):
    verdicts = [c for c in pr.comments_by(spec.get("authors")) if "<!-- reef-verdict -->" in c["body"]]
    verdict = parse_reef(verdicts[-1]["body"]) if verdicts else None
    url = verdicts[-1]["html_url"] if verdicts else None
    found = check_state(pr, spec["check"])
    if found and found[0] == "running":
        return gate(spec, "running", f"{spec['check']} {found[1]}")
    if not verdict or verdict["head"] != pr.head:
        if found:
            return gate(spec, "waiting", f"{spec['check']} {found[1]}, but no verdict covers this commit")
        return not_started(pr, spec, "Reef review")
    summary = f"{verdict['conclusion'] or 'no conclusion'}, risk {verdict['risk'] or 'unknown'}"
    items = [{"key": f"reef:{f['id']}@{pr.head[:12]}", "kind": "reef", "finding": f["id"], "file": f["file"],
              "title": f["text"][:200], "detail": f["text"], "section": f["section"], "url": url,
              "optional": not (f["section"] or "").lower().startswith("to fix")}
             for f in verdict["findings"]]
    items += threads_for(pr, spec, "reef-thread")
    failed = verdict["conclusion"] not in spec.get("pass_conclusions", ["no_blockers"])
    blocking = [i for i in items if not i.get("optional")]
    return gate(spec, "fail" if failed or blocking else "pass", summary, items)


QA_REPORT = re.compile(r"<!-- visual-qa-report:1 (\{.*\}) -->")
QA_WAIVE = re.compile(r"^\s*waive:\s*(.+)$", re.MULTILINE)


def qa_row(body, case_id):
    """Expected and actual of a case, from its row in the report's tables (the JSON lacks them)."""
    for line in body.splitlines():
        if f"**{case_id}**" in line and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if len(cells) >= 6:
                return {"expected": cells[3], "actual": cells[4]}
    return {}


def qa_gate(pr, spec):
    if pr.labels & set(spec.get("skip_labels", [])):
        return gate(spec, "pass", "skipped by label")
    report, url, body = None, None, ""
    for comment in pr.comments_by(spec.get("authors")):
        match = QA_REPORT.search(comment["body"])
        if match:
            report, url, body = json.loads(match.group(1)), comment["html_url"], comment["body"]
    found = check_state(pr, spec["check"])
    run = pr.check_runs.get(spec["check"]) or {}
    title = (run.get("output") or {}).get("title") or ""
    if found and found[0] == "running":
        return gate(spec, "running", f"{spec['check']}: {title or found[1]}")
    if not report or report.get("headSha") != pr.head:
        if found and found[0] == "pass" and "skip" in title.lower():
            return gate(spec, "pass", title)
        if found:
            return gate(spec, "waiting", f"no QA report on this commit; check says: {title or found[1]}")
        return not_started(pr, spec, "QA")
    waived = set()
    for comment in pr.comments:
        if comment["body"].lstrip().startswith("@qa"):
            for line in QA_WAIVE.findall(comment["body"]):
                waived.update(c.strip() for c in line.split(",") if c.strip())
    counts, items = {}, []
    for case in report.get("cases", []):
        counts[case["status"]] = counts.get(case["status"], 0) + 1
        if case["status"] in ("fail", "blocked") and case["id"] not in waived:
            items.append({"key": f"qa:{case['id']}@{pr.head[:12]}", "kind": f"qa-{case['status']}",
                          "case": case["id"], "title": case.get("title"), "section": case.get("section"),
                          "evidence": case.get("evidence", []), "excerpt": case.get("excerpt"), "url": url,
                          **qa_row(body, case["id"])})
    blocked_waived = sum(1 for c in report.get("cases", []) if c["status"] == "blocked" and c["id"] in waived)
    summary = ", ".join(f"{n} {s}" for s, n in sorted(counts.items()))
    if waived:
        summary += f"; waived {', '.join(sorted(waived))}"
    result = gate(spec, "fail" if items else "pass", summary, items)
    result["blocked_waivers_left"] = max(spec.get("max_blocked", 0) - blocked_waived, 0)
    return result


def human_gate(pr, spec):
    ignored = spec.get("ignore_authors", [])
    markers = spec.get("ignore_body_markers", [])

    def is_human(user, body=""):
        login = user.get("login")
        return (user.get("type", user.get("__typename")) == "User" and not pr.ours(login)
                and not matches(login, ignored) and not any(m in (body or "") for m in markers))

    latest, reviewed_head = {}, False
    for review in sorted(pr.reviews, key=lambda r: r.get("submitted_at") or ""):
        if not is_human(review["user"], review.get("body")):
            continue
        reviewed_head = reviewed_head or review.get("commit_id") == pr.head
        if review["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[review["user"]["login"]] = review
    approvals = sorted(login for login, r in latest.items() if r["state"] == "APPROVED")
    items = [{"key": f"review:{r['id']}", "kind": "changes-requested", "author": login,
              "title": (r.get("body") or "").strip()[:200], "detail": (r.get("body") or "").strip()[:DETAIL_LIMIT],
              "url": r["html_url"]}
             for login, r in latest.items() if r["state"] == "CHANGES_REQUESTED"]
    items += [thread_item(t, a, f, "thread") for t, a, f in pr.unanswered_threads()
              if is_human({"login": a.get("login"), "type": a.get("__typename")})]
    for n, comment in enumerate(pr.comments):
        body = comment["body"].lstrip()
        if not is_human(comment["user"], body) or body.startswith(("@qa", "/")):
            continue
        if any(pr.ours(c["user"]["login"]) for c in pr.comments[n + 1:]):
            continue
        items.append({"key": f"comment:{comment['id']}", "kind": "comment", "author": comment["user"]["login"],
                      "title": body.splitlines()[0][:200] if body else "", "detail": body[:DETAIL_LIMIT],
                      "url": comment["html_url"]})
    need = spec.get("min_approvals", 1)
    summary = f"{len(approvals)}/{need} approvals" + (f" ({', '.join(approvals)})" if approvals else "")
    summary += "; reviewed this commit" if reviewed_head else "; no review on this commit"
    if items:
        return gate(spec, "fail", summary, items)
    return gate(spec, "pass" if len(approvals) >= need else "waiting", summary)


KINDS = {"checks": checks_gate, "reef": reef_gate, "visual-qa": qa_gate, "human": human_gate}


def overall(pr, gates):
    state, mergeable = pr.view["state"], pr.view.get("mergeable")
    if state == "MERGED":
        return "merged", []
    if state == "CLOSED":
        return "closed", []
    if mergeable == "CONFLICTING":
        return "conflict", []
    statuses = {g["id"]: g["status"] for g in gates}
    if "running" in statuses.values():
        return "running", [i for i, s in statuses.items() if s == "running"]
    waiting = [i for i, s in statuses.items() if s == "waiting"]
    if waiting:
        return "stalled", waiting
    if "fail" in statuses.values():
        return "round-needed", []
    return "ready", []


def print_summary(result):
    waiting = f" (waiting on {', '.join(result['waiting_on'])})" if result["waiting_on"] else ""
    print(f"{result['url']} @ {result['head'][:7]}: {result['overall']}{waiting}")
    for g in result["gates"]:
        items = f" [{len(g['items'])} items]" if g["items"] else ""
        print(f"  {g['id']:<6} {g['status']:<8} {g['summary']}{items}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("pr", nargs="?")
    parser.add_argument("--repo", help="owner/repo, when the PR is a number")
    parser.add_argument("--gates", help="a gates file, instead of the one matching the remote")
    parser.add_argument("--me", help="the GitHub login running the watcher (default: gh's user)")
    parser.add_argument("--summary", action="store_true", help="one line per gate instead of JSON")
    parser.add_argument("--show", metavar="FILE", help="print the summary of a saved result; reads nothing else")
    args = parser.parse_args()
    if args.show:
        return print_summary(json.load(open(args.show)))
    if not args.pr:
        parser.error("a PR is required")

    match = re.match(r"https://(github\.com)/([^/]+/[^/]+)/pull/(\d+)", args.pr)
    if match:
        host, repo, number = match.groups()
    elif args.repo and args.pr.isdigit():
        host, repo, number = "github.com", args.repo, args.pr
    else:
        sys.exit("pr-gates: pass a PR URL, or a number with --repo owner/repo")

    gates_file, config = find_gates(f"{host}/{repo}", args.gates)
    pr = PR(repo, int(number), args.me)
    gates = [KINDS[spec["kind"]](pr, spec) for spec in config["gates"]]
    state, waiting_on = overall(pr, gates)
    result = {"pr": int(number), "url": pr.view["url"], "state": pr.view["state"], "draft": pr.view["isDraft"],
              "head": pr.head, "head_age_minutes": round(pr.head_age), "branch": pr.view["headRefName"],
              "base": pr.view["baseRefName"], "mergeable": pr.view.get("mergeable"),
              "auto_merge": bool(pr.view.get("autoMergeRequest")), "overall": state,
              "waiting_on": waiting_on, "gates": gates, "gates_file": gates_file or "default"}
    # What the watcher compares with what it last acted on: a change here is news.
    result["signature"] = "|".join([state, pr.head, ",".join(waiting_on)]
                                   + sorted(i["key"] for g in gates for i in g["items"]))
    if args.summary:
        print_summary(result)
    else:
        json.dump(result, sys.stdout, indent=1)
        print()


if __name__ == "__main__":
    main()
