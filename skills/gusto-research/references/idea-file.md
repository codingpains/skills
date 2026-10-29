# Idea files

Each idea is one file, `$GUSTO_HOME/ideas/<YYYY-MM-DD>-<slug>.md`. The slug
is the Spanish working title in kebab case without accents. Later skills
(script, preproduction, editing) pick up an idea from here and move its
`status:` forward, so this format is a contract. Change it only together
with them.

Text that ends up in the video (titles, hook, talking points, on-screen
words) is in Spanish, for a Mexican and Latin American audience. Notes to
Gustavo are in English.

```markdown
---
title: "7 cosas que un hombre elegante nunca hace en una boda"
bucket: grow            # grow | loyal | interact | experiment
pillar: style           # style | fitness | charisma
status: proposed        # proposed | chosen | scripted | shot | published | parked | rejected
created: 2026-10-29
series:                 # loyal ideas: "<series name> 1/4"; else empty
links_to: [_NG8gyjc1yA, qcIdvHc3OVs]   # back-catalogue videos referenced inside the video, all [k]
cta: qcIdvHc3OVs        # the one "watch this next" video at the end, [k]
video_id:               # filled in when published
confidence: 2           # 1–3, see "Confidence" below
---

## Por qué ahora   (English: why this, why now)
The evidence, with numbers and dates: search demand, top results and their
age, the channel's own record on the topic, audience requests (quoted, with
the author and video), competitors' recent results, the source article.

## Títulos
3 options. At least one uses the words people search for (from autocomplete).

## Gancho (primeros 15 segundos)
What he says and what the viewer sees.

## Puntos clave
5–8 beats. Each beat names the visual: outfit change, side-by-side,
on-screen text, B-roll. Mark where each `links_to` video is mentioned and why
it fits there.

## Outfits
Every outfit the video needs, described piece by piece (garment, colour,
fabric, fit), with a reference image URL from the research (GQ, Pitti street
style, Popeye). He records in black jeans and a black T-shirt and the outfits
are swapped in with AI, so no outfit depends on his wardrobe. Mark which
pieces belong to the ~20 core pieces and which are trend pieces.

## Shorts
4–5 moments that stand alone in under 60 seconds, each with its first line.

## Experto vs. Gusto
Where the sources and his mottos agree, and where he will disagree on camera.

## Fuentes
URLs with dates.

## Resultados   (filled in after publishing)
7-day and 28-day numbers from analytics.py, compared with the channel median
for the same age, and one line on what it teaches.
```

## Buckets

- **grow** — for people who have never seen the channel. A broad topic people
  search for. It must reference 1–3 `[k]` back-catalogue videos at the moments
  where they help, and end on one `cta` video that continues the viewer's
  question.
- **loyal** — for regulars. Comes from their comments and from open loops
  (unfinished series). Planned as a series of 3–5 parts; each part's file
  carries `series:`.
- **interact** — Q&A, reviewing subscribers' outfits, reacting to their
  photos. Needs a call for submissions 2–3 weeks before recording: the idea
  says where (a Short, a community post, a pinned comment) and by when.
- **experiment** — a format the channel has never tried. States the
  hypothesis ("a 7-day athlete challenge vlog keeps retention above X") and
  what result would make it worth repeating.

## Confidence

1. One signal, or signals that disagree.
2. Two independent signals agree (e.g. search demand plus an old hit on the topic).
3. Three or more agree, including either one of the channel's own numbers or a regular's request.
