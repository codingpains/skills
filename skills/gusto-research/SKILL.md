---
name: gusto-research
description: "Research YouTube video ideas for Gustavo's Spanish-language channel Gusto Clásico (men's style, fitness, charisma, with a classic masculine tone). Reads the channel's own numbers, its regulars' comments, Spanish-language competitors, YouTube search demand and expert sources (GQ, Put This On, Japanese and Italian style, evidence-based fitness, the Stoics), then proposes evidence-backed ideas in four buckets: grow the audience, serve loyal viewers with 3–5 part series, interact with them, and rare format experiments. Each idea links to old videos he still stands by and lists its outfits and Shorts. Writes one idea file per idea for the script and preproduction skills. Use when Gustavo asks for video ideas, topics, 'what should my next video be', a monthly content plan, or how published videos performed. Invoke as /gusto-research [focus or topic] | learn | setup-analytics."
argument-hint: "[focus or topic] | learn | setup-analytics"
---

# /gusto-research

Gustavo publishes one long video a month on Gusto Clásico and cuts 4–5
Shorts from it. He wants ideas he can trust: each one backed by evidence,
faithful to his mottos, and built to bring viewers back for another video.

Arguments: `$ARGUMENTS`.

- Empty, or free text: a research run. Free text is a **focus** ("ideas for
  December", "fitness only", "something with Humberto"); it steers the run.
- `learn`: only step 2's results loop, no new ideas.
- `setup-analytics`: walk him through § Analytics setup.

## Rules

- **Evidence, not taste.** Every idea cites numbers and dates. "Seems
  popular" without a number is not evidence.
- **His mottos win.** An idea that contradicts `channel.md` is dropped or
  reframed so that he disagrees on camera.
- **Never send a viewer to a video he has not cleared.** `links_to` and
  `cta` hold only `[k]` videos from `catalogue-review.md`. If too few are
  marked, say so and propose the link anyway, marked "(unreviewed)".
- **No duplicates.** Check the catalogue before proposing. A topic he
  already covered is either a remake (`[r]`, or a big old hit worth
  redoing) or a new angle that says what is new.
- **Spanish on camera, English to him.** See `references/idea-file.md`.
- **Nothing is published or posted anywhere.** This skill reads public data
  and his own analytics, and writes only to the home folder.
- **Never print or ask in chat for secrets.** Analytics credentials live in
  `$GUSTO_HOME/secrets/`.

## Files

Home folder: `$GUSTO_HOME`, else `~/.gusto-clasico/`. What each file holds:
`references/home-folder.md`. Scripts live in
`~/.claude/skills/gusto-research/scripts/`; run them with `python3`, and
`--help` explains each one. They need `yt-dlp` on the PATH
(`brew install yt-dlp`).

## 1. Load

Read `channel.md`, `learnings.md`, `catalogue-review.md`, the latest file in
`runs/`, and the frontmatter of every file in `ideas/`. From the ideas, work out:

- the open series and which part is next;
- the published bucket and pillar mix of the last 12 long videos, against
  the targets in `channel.md`;
- how many experiments were published in the last 20;
- which ideas were proposed earlier and are still `proposed` or `parked`.
  Re-offer them only with fresh evidence.

## 2. Refresh the data

Run these. Then mention in one line any step that failed and carry on.

1. `catalogue.py`. Run it with `--full` if the catalogue is older than 90 days.
2. `comments.py --recent 20`. This writes `audience.md`.
3. If `secrets/token.json` exists:
   - Run `analytics.py channel --days 90`.
   - For each published idea (`video_id` set) that is missing a 7-day or
     28-day result it is now old enough for, run
     `analytics.py video <id> --days 7|28`.
   - Write the numbers into the idea's `## Resultados` section. Add one dated
     line to the top of `learnings.md` saying what it teaches, e.g.
     "2026-12-04: grow / style: 62% of views from non-subscribers, CTA video
     got 4% of its views from end screens. The search-led title worked."
   - Also read any CSV he dropped in `analytics/studio/`.

   No token: say "analytics not connected" once and go on with public data.
4. If `catalogue-review.md` is missing, or more than 20% of it is unmarked,
   run `review_list.py`. Ask him to mark it, and tell him how many are still
   `[ ]`.

`learn` stops here and reports what the results taught.

## 3. Research

Plan for the month the video will **come out**, about 4–6 weeks from now.
In Mexico that means the season, the holidays (posadas, Christmas and New
Year parties, New Year resolutions, Valentine's Day, Father's Day in June,
weddings and graduations), and the weather in Mexico.

Work through these, in this order:

1. **The audience.** From `audience.md`, list what regulars ask for or
   complain about. Look for repeated themes, unanswered questions and open
   loops: a "Parte 1" with no Parte 2, a series that stopped.
   - Known open loops as of 2026-10: "100 tips de estilo" stopped at
     Parte 4; "Guía para empezar el gimnasio" never got a Parte 2.
2. **The channel's own record.** In `catalogue.jsonl`, find the topics and
   title patterns that won. Compare views per year of age, because old
   videos have had more time. Look for topics that had big views and have
   not been touched in years.
3. **Competitors.** Run `market.py channel <handle> --n 20` for each
   competitor in `channel.md`. Look for what is hot right now, and for
   topics where they do well but the advice clashes with his mottos: those
   are chances for him to give a better answer.
4. **Search demand.** For each pillar, run `market.py suggest` with 3–5 seed
   phrases, and with `--expand` on the most promising one. For each
   candidate topic, run `market.py search "<query>"`.
   - High views on results that are old or from small channels: demand that
     nobody serves well.
   - The top results all over 1M and from a big competitor: hard to win.
     Pick a narrower angle.
5. **Expert sources.** Search `references/sources.md` for the coming season
   and each candidate topic. Collect outfit reference images: GQ, Pitti street
   style, Popeye. Note the URL and date of each.
6. **Old videos to link.** For each candidate, pick the `[k]` videos it can
   reference. When the exact moment matters, `transcript.py <id>` shows what
   the old video actually says.

If the run has a focus, give it most of the time, but still check steps 1
and 2.

## 4. Pick the ideas

Draft about 12 candidates. Then cut to the shortlist using the bucket and
pillar targets in `channel.md` against the mix from step 1:

| Bucket | Per run |
|---|---|
| grow | 3 |
| loyal | 2, each as a series outline (3–5 parts, part 1 in full) |
| interact | 1 |
| experiment | 1, only if fewer than 1 of the last 20 published was an experiment; else 0 |

Each idea must pass every check for its bucket in `references/idea-file.md`.
On top of that:

- **grow:** the title uses words people actually search for. It names the
  link moments and the `cta`. And the viewer is someone who has never heard
  of him.
- **loyal:** it quotes at least one regular's comment, with the author and
  the video.
- **experiment:** it names a format the catalogue shows he has never done.
  Check titles and playlists.
- **Everything:** it can be shown, not just told. List the outfit changes,
  side-by-sides and on-screen examples. It also yields 4–5 Shorts.

Rank the shortlist by confidence, then by fit with the mix.

## 5. Present and save

1. Write every shortlisted idea to `ideas/` as `status: proposed`, in the
   format of `references/idea-file.md`.
2. In chat, open with one line on the state of the channel: the latest
   numbers, and what changed since the last run. Then give each idea in
   five lines or fewer:
   - bucket and pillar
   - the best title
   - why now, with numbers
   - links and `cta`
   - confidence and the file path
3. End with your recommendation for next month's video and one sentence on
   why.
4. Write `runs/<date>.md`. List what was read: the competitor handles, the
   queries, the sources. Then the shortlist, and the next run's open
   questions.

When he chooses, set the chosen idea to `status: chosen`, along with any
series parts that go with it. Set ideas he turns down to `rejected`, and
add his reason to the file when he gives one. Mention in one line that the
next step is the script skill, which reads the `chosen` idea.

## Analytics setup

Do this when he runs `setup-analytics`, or when he agrees to connect after a
run says "analytics not connected". Give him the steps one at a time, and
wait for each one to be done:

1. Go to console.cloud.google.com. Create a project, e.g. "Gusto Clásico".
2. Under APIs & Services → Library, enable **YouTube Analytics API** and
   **YouTube Data API v3**.
3. Set up the OAuth consent screen (Google Auth Platform):
   - User type: External. Add his Google account as a test user.
   - Then set publishing status to **In production**. Otherwise Google
     expires the sign-in every 7 days. It will show an "unverified app"
     warning, which is fine for his own use: Advanced → continue.
4. Under Credentials → Create credentials → OAuth client ID, choose type
   **Desktop app**. Download the JSON and save it as
   `~/.gusto-clasico/secrets/client_secret.json`.
5. Run `analytics.py auth`. A browser opens. He signs in with the Google
   account that owns the channel: if the channel is a Brand Account, he
   picks the channel when asked.
6. Run `analytics.py channel --days 28` and show the summary. That confirms
   it works.

Impressions and click-through rate are not in the API. For those, he
exports from YouTube Studio → Analytics → Advanced mode → Export, into
`~/.gusto-clasico/analytics/studio/`.
