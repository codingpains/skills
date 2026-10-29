# The home folder

`$GUSTO_HOME`, else `~/.gusto-clasico/`. Private to Gustavo; never commit it
to the skills repo. Every Gusto Clásico skill shares it.

| Path | Written by | What |
|---|---|---|
| `channel.md` | Gustavo (and Claude when he says so) | Mottos, pillar and bucket mix, tone, format, cadence, competitors. Read first, every run. |
| `catalogue.jsonl` | `catalogue.py` | Every upload: id, kind, date, views, likes, comments, duration, title. |
| `catalogue-review.md` | `review_list.py`, then Gustavo | Which old videos he stands by: `[k]` keep, `[o]` outdated, `[r]` remake. |
| `comments/<id>.json`, `audience.md` | `comments.py` | Raw comments; digest of regulars and their requests. |
| `transcripts/<id>.txt` | `transcript.py` | Plain-text transcripts, his and other channels'. |
| `analytics/` | `analytics.py` | Raw Analytics reports. `analytics/studio/` holds CSVs he exports from YouTube Studio (impressions, click-through rate). |
| `secrets/` | `analytics.py auth` | OAuth client and token, mode 600. Never print them. |
| `ideas/<date>-<slug>.md` | this skill, then the later skills | One file per idea; format in `idea-file.md`. |
| `runs/<date>.md` | this skill | What each run looked at and proposed, and what he chose. |
| `learnings.md` | this skill | What published videos taught: one dated line each, newest first. |

## When `channel.md` is missing

Ask Gustavo once for: mottos per pillar, pillar shares, tone, format, cadence
and bucket mix. Write them in the same sections, with the channel URL on a
`channel:` line in the frontmatter.
