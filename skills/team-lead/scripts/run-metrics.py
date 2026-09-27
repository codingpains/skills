#!/usr/bin/env python3
"""Measure one /team-lead run from Claude Code's session transcripts.

    run-metrics.py --ticket ONB-123 [--since 2026-09-24T10:00:00Z]
                   [--sessions a.jsonl,b.jsonl] [--json out.json] [--md out.md]

Finds every main-session transcript under ~/.claude/projects that invoked
`/team-lead <ticket>` (a run resumed with --from spans several sessions),
takes each one from that invocation onward, adds the subagents it spawned,
and reports per agent: wall time, turns, tokens by kind, peak context,
estimated cost, tool calls by tool, the heaviest and slowest tool results,
repeated calls and errors. The team-assessor's own work is left out. Time the Lead spent waiting on the human
(AskUserQuestion, or a typed message), and time a subagent sat idle between handing back and being resumed,
is reported apart, so it never reads as a bottleneck.

Tool-result tokens are estimated as characters / 4. Cost uses
~/.claude/pricing-cache.json (USD per million tokens) when it exists.
Reads only; writes nothing but the --json and --md files.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys
from datetime import datetime

PROJECTS = os.path.expanduser("~/.claude/projects")
PRICING = os.path.expanduser("~/.claude/pricing-cache.json")
TOP = 8
# Models the pricing cache is known to lack. Without an entry, price_for falls
# back to the family (claude-opus-5-5 -> claude-opus-5) and bills the old rates.
KNOWN_PRICES = {
    "claude-opus-5-5": {"input": 4.0, "cache_write_5m": 5.0, "cache_write_1h": 8.0, "cache_read": 0.20, "output": 20.0},
}


def ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def load(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def pricing():
    try:
        cached = json.load(open(PRICING)).get("models", {})
    except (OSError, ValueError):
        cached = {}
    return {**KNOWN_PRICES, **cached}


def price_for(model, table):
    """Exact model id, else drop trailing -N parts: claude-opus-5-5 -> claude-opus-5."""
    name = re.sub(r"\[.*\]$", "", model or "")
    while name:
        if name in table:
            return table[name]
        if not re.search(r"-\d+$", name):
            return None
        name = re.sub(r"-\d+$", "", name)
    return None


def summarize_input(name, inp):
    inp = inp or {}
    for key in ("command", "file_path", "pattern", "description", "query", "skill", "url", "path"):
        if key in inp:
            return " ".join(f"{key}={inp[key]}".split())[:140]
    return " ".join(json.dumps(inp).split())[:140]


def is_tool_result(r):
    content = (r.get("message") or {}).get("content")
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def is_human_turn(r):
    """A message the human typed, as opposed to a tool result, injected context,
    or the notice that a background agent finished."""
    if r.get("type") != "user" or r.get("isMeta") or r.get("isSidechain") or is_tool_result(r):
        return False
    content = (r.get("message") or {}).get("content")
    text = content if isinstance(content, str) else " ".join(
        b.get("text", "") for b in content or [] if isinstance(b, dict))
    return not text.lstrip().startswith("<task-notification>")


def ended_turn(r):
    """An assistant message that calls no tool: the agent has handed back."""
    content = (r.get("message") or {}).get("content")
    return not (isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_use" for b in content))


def text_len(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(c.get("text", "")) if isinstance(c, dict) else len(str(c)) for c in content)
    return len(str(content or ""))


def analyze(rows, label, kind, table, start=None):
    rows = [r for r in rows if not start or (r.get("timestamp") and ts(r["timestamp"]) >= start)]
    stamps = [ts(r["timestamp"]) for r in rows if r.get("timestamp")]
    usage, models, peak = collections.Counter(), collections.Counter(), 0
    seen, cost, calls, first_prompt = set(), 0.0, {}, 0
    human_wait, prev, handed_back = 0.0, None, False
    for r in rows:
        now = ts(r.get("timestamp"))
        if prev and now and r.get("type") == "user":
            # The Lead waits on a human message. A subagent that handed back and
            # is later resumed (SendMessage after an escalation) was idle meanwhile.
            if (kind == "lead" and is_human_turn(r)) or (kind == "subagent" and handed_back and not is_tool_result(r)):
                human_wait += (now - prev).total_seconds()
                prev = now  # the wait ended here; a second message in a row adds only its own gap
        if r.get("type") == "assistant" and now:
            prev, handed_back = now, ended_turn(r)
        msg = r.get("message") or {}
        if r.get("type") == "user" and not first_prompt and isinstance(msg.get("content"), str):
            first_prompt = len(msg["content"])
        if r.get("type") != "assistant":
            if r.get("type") == "user" and isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        call = calls.get(block.get("tool_use_id"))
                        if call:
                            call["chars"] = text_len(block.get("content"))
                            call["error"] = bool(block.get("is_error"))
                            call["end"] = ts(r.get("timestamp"))
            continue
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls[block["id"]] = {
                    "id": block["id"], "name": block.get("name"),
                    "input": summarize_input(block.get("name"), block.get("input")),
                    "raw": block.get("input") or {}, "start": ts(r.get("timestamp")),
                    "chars": 0, "error": False, "end": None,
                }
        mid = msg.get("id") or r.get("requestId")
        if not mid or mid in seen or not msg.get("usage"):
            continue
        seen.add(mid)
        u = msg["usage"]
        cc = u.get("cache_creation") or {}
        write_1h = cc.get("ephemeral_1h_input_tokens", 0)
        write_5m = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - write_1h)
        part = {
            "input": u.get("input_tokens", 0), "cache_write_5m": write_5m, "cache_write_1h": write_1h,
            "cache_read": u.get("cache_read_input_tokens", 0), "output": u.get("output_tokens", 0),
        }
        usage.update(part)
        models[msg.get("model", "?")] += 1
        peak = max(peak, part["input"] + part["cache_read"] + write_5m + write_1h)
        p = price_for(msg.get("model"), table)
        if p:
            cost += sum(part[k] * p.get(k, 0) for k in part) / 1e6

    by_tool = collections.defaultdict(lambda: {"calls": 0, "errors": 0, "result_tokens": 0, "seconds": 0.0})
    repeats = collections.Counter()
    for c in calls.values():
        secs = (c["end"] - c["start"]).total_seconds() if c["end"] and c["start"] else 0.0
        c["seconds"] = secs
        c["result_tokens"] = c["chars"] // 4
        t = by_tool[c["name"]]
        t["calls"] += 1
        t["errors"] += c["error"]
        t["result_tokens"] += c["result_tokens"]
        t["seconds"] += secs
        repeats[(c["name"], c["input"])] += 1
        if c["name"] == "AskUserQuestion":
            human_wait += secs

    def brief(c):
        return {k: c[k] for k in ("name", "input", "result_tokens", "seconds", "error")}

    wall = (max(stamps) - min(stamps)).total_seconds() if stamps else 0.0
    return {
        "label": label, "kind": kind,
        "start": min(stamps).isoformat() if stamps else None,
        "wall_seconds": round(wall), "human_wait_seconds": round(human_wait),
        "active_seconds": round(wall - human_wait),
        "turns": len(seen), "models": dict(models), "tokens": dict(usage),
        "total_tokens": sum(usage.values()), "peak_context": peak, "cost_usd": round(cost, 2),
        "handoff_tokens": first_prompt // 4 if kind == "subagent" else None,
        "tools": {k: dict(v, seconds=round(v["seconds"])) for k, v in sorted(by_tool.items(), key=lambda kv: -kv[1]["result_tokens"])},
        "heaviest_results": [brief(c) for c in sorted(calls.values(), key=lambda c: -c["chars"])[:TOP]],
        "slowest_calls": [brief(c) for c in sorted(calls.values(), key=lambda c: -c["seconds"])[:TOP] if c["name"] not in ("AskUserQuestion", "Agent")],
        "repeated_calls": [{"name": n, "input": i, "times": k} for (n, i), k in repeats.most_common() if k > 1][:TOP],
        "errors": [brief(c) for c in calls.values() if c["error"]][:TOP],
        "agent_calls": [{"id": c["id"], "type": c["raw"].get("subagent_type"), "description": c["raw"].get("description"), "seconds": round(c["seconds"])} for c in calls.values() if c["name"] == "Agent"],
    }


def find_sessions(ticket, since, root):
    pattern = re.compile(r"<command-name>/?team-lead</command-name>.*?<command-args>[^<]*\b" + re.escape(ticket) + r"\b", re.I | re.S)
    found = []
    for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
        if since and datetime.fromtimestamp(os.path.getmtime(path)).astimezone() < since:
            continue
        with open(path, errors="ignore") as fh:
            if pattern.search(fh.read()):
                found.append(path)
    return sorted(found, key=os.path.getmtime)


def invocation_start(rows, ticket):
    pattern = re.compile(r"<command-args>[^<]*\b" + re.escape(ticket) + r"\b", re.I)
    for r in rows:
        content = (r.get("message") or {}).get("content")
        text = content if isinstance(content, str) else json.dumps(content or "")
        if r.get("type") == "user" and "team-lead" in text and pattern.search(text):
            return ts(r.get("timestamp"))
    return None


def fmt_secs(s):
    s = int(s or 0)
    return f"{s // 3600}h{s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"


def fmt_k(n):
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.1f}k" if n >= 1e3 else str(n)


def cell(text):
    return text.replace("|", "\\|").replace("`", "'")


def markdown(report):
    t = report["totals"]
    out = [f"# Run metrics — {report['ticket']}", "",
           f"Sessions: {len(report['sessions'])}. Wall time {fmt_secs(t['wall_seconds'])}, of which waiting on the human {fmt_secs(t['human_wait_seconds'])}. "
           f"Tokens {fmt_k(t['total_tokens'])} (cache read {fmt_k(t['cache_read'])}). Estimated cost ${t['cost_usd']:.2f}.", "",
           "## Per agent", "",
           "| Agent | Model | Active | Turns | Tool calls | Input+cache write | Cache read | Output | Peak context | Handoff | Cost | Errors |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in report["agents"]:
        tok = a["tokens"]
        write = tok.get("input", 0) + tok.get("cache_write_5m", 0) + tok.get("cache_write_1h", 0)
        calls = sum(v["calls"] for v in a["tools"].values())
        errs = sum(v["errors"] for v in a["tools"].values())
        model = ", ".join(sorted(a["models"])) or "?"
        out.append(f"| {a['label']} | {model} | {fmt_secs(a['active_seconds'])} | {a['turns']} | {calls} | {fmt_k(write)} | "
                   f"{fmt_k(tok.get('cache_read', 0))} | {fmt_k(tok.get('output', 0))} | {fmt_k(a['peak_context'])} | "
                   f"{fmt_k(a['handoff_tokens']) if a['handoff_tokens'] else '—'} | ${a['cost_usd']:.2f} | {errs} |")
    sections = [("Heaviest tool results (tokens pulled into context)", "heaviest_results", "result_tokens"),
                ("Slowest tool calls", "slowest_calls", "seconds")]
    for title, key, metric in sections:
        rows = sorted(((a["label"], c) for a in report["agents"] for c in a[key]), key=lambda x: -x[1][metric])[:12]
        out += ["", f"## {title}", "", "| Agent | Tool | Input | Tokens | Seconds |", "|---|---|---|---|---|"]
        out += [f"| {lbl} | {c['name']} | `{cell(c['input'])}` | {fmt_k(c['result_tokens'])} | {int(c['seconds'])} |" for lbl, c in rows]
    reps = [(a["label"], r) for a in report["agents"] for r in a["repeated_calls"]]
    out += ["", "## Repeated identical calls", ""]
    out += [f"- {lbl}: {r['name']} ×{r['times']} `{cell(r['input'])}`" for lbl, r in reps] or ["None."]
    errs = [(a["label"], e) for a in report["agents"] for e in a["errors"]]
    out += ["", "## Failed tool calls", ""]
    out += [f"- {lbl}: {e['name']} `{cell(e['input'])}`" for lbl, e in errs] or ["None."]
    out += ["", "## Tokens by tool, per agent", ""]
    for a in report["agents"]:
        tools = ", ".join(f"{n} {v['calls']}× {fmt_k(v['result_tokens'])}" for n, v in list(a["tools"].items())[:8])
        out.append(f"- **{a['label']}**: {tools or 'no tools'}")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ticket", required=True)
    ap.add_argument("--since", help="ISO time; ignore transcripts not modified since (the run's started_at)")
    ap.add_argument("--sessions", help="comma-separated main-session transcripts; skips the search")
    ap.add_argument("--projects", default=PROJECTS, help="transcripts root (default ~/.claude/projects)")
    ap.add_argument("--json")
    ap.add_argument("--md")
    args = ap.parse_args()

    since = ts(args.since) if args.since else None
    sessions = args.sessions.split(",") if args.sessions else find_sessions(args.ticket, since, args.projects)
    if not sessions:
        sys.exit(f"run-metrics: no session invoking /team-lead {args.ticket} found under {args.projects}")

    table = pricing()
    agents = []
    for n, path in enumerate(sessions, 1):
        rows = load(path)
        start = invocation_start(rows, args.ticket) or since
        suffix = f" (session {n})" if len(sessions) > 1 else ""
        lead = analyze(rows, "lead" + suffix, "lead", table, start)
        agents.append(lead)
        stage_of = {c["id"]: c for c in lead["agent_calls"]}
        sub_dir = os.path.join(path[:-len(".jsonl")], "subagents")
        subs = []
        for sub in glob.glob(os.path.join(sub_dir, "agent-*.jsonl")):
            meta_path = sub[:-len(".jsonl")] + ".meta.json"
            meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
            if meta.get("agentType") == "team-assessor":
                continue  # the measurement, not the pipeline
            call = stage_of.get(meta.get("toolUseId"))
            if not call and start:
                first = next((ts(r["timestamp"]) for r in load(sub) if r.get("timestamp")), None)
                if not first or first < start:
                    continue
            label = f"{meta.get('agentType', 'agent')}: {meta.get('description', os.path.basename(sub))}{suffix}"
            subs.append(analyze(load(sub), label, "subagent", table))
        agents += sorted(subs, key=lambda a: a["start"] or "")

    keys = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
    leads = [a for a in agents if a["kind"] == "lead"]
    totals = {k: sum(a["tokens"].get(k, 0) for a in agents) for k in keys}
    totals.update(
        total_tokens=sum(a["total_tokens"] for a in agents),
        cost_usd=round(sum(a["cost_usd"] for a in agents), 2),
        wall_seconds=sum(a["wall_seconds"] for a in leads),
        human_wait_seconds=sum(a["human_wait_seconds"] for a in leads),
    )
    report = {"ticket": args.ticket, "sessions": sessions, "totals": totals, "agents": agents}
    for a in agents:
        a.pop("agent_calls", None)
    if args.json:
        json.dump(report, open(args.json, "w"), indent=2, default=str)
    md = markdown(report)
    if args.md:
        open(args.md, "w").write(md)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
