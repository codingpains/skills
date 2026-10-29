---
name: gusto-script
description: "Turn one chosen Gusto Clásico video idea into a recording-ready script in Latin American Spanish, plus a storyboard that shows how the edit should go. Researches the single topic in depth first (his own old videos and what he said in them, the comments, the top competing videos and their transcripts, expert articles, peer-reviewed studies, the style rulebook), then writes the script in Gustavo's own voice, scene by scene, with on-screen text, edit notes, link moments, the CTA and the Shorts. Storyboard frames start from original images found in the research (kept untouched, with their sources), and generative AI puts Gustavo, from his own footage and his own set, into each outfit. Reads the idea files /gusto-research writes. Use when Gustavo asks for a script, 'guion', a storyboard, or to move a chosen idea forward. Invoke as /gusto-script [idea slug or path] [notes] | self."
argument-hint: "[idea slug or path] [notes] | self"
---

# /gusto-script

Second step of the Gusto Clásico pipeline: research → **script** →
preproduction → editing. It takes one idea from `/gusto-research` and
produces everything Gustavo needs to record it and his editor needs to cut
it: a deeper research file, the script, and a storyboard with images of
him in each outfit.

Arguments: `$ARGUMENTS`.

- Empty: the idea with `status: chosen`. Several chosen: the next part of
  the open series, else the oldest. None: list the `proposed` ideas (title,
  bucket, confidence) and ask which. Setting it to `chosen` follows
  `/gusto-research`'s rules, including the scientific-evidence bar.
- An idea slug, a file name or a path: that idea.
- Free text after it: his notes for a revision ("más corto", "cambia el
  gancho", "regenera el cuadro 07"). If the production already exists,
  revise it, don't start over: § 6.
- `self`: (re)build the self pack only, § Self pack.

## Rules

- **The idea is the brief, the research is the authority.** Keep its
  title, bucket, rules, `links_to` and `cta` unless the deeper research
  shows one is wrong. Then change it and say why in `research.md`
  § Lo que cambió.
- **Every fact on camera has a source.** Style advice stands on a rule in
  `rules.md` or a source in `research.md`. Numbers, dates and quotes come
  with their URL. Any claim about the body needs a verified row in the
  idea's `## Evidencia científica`, held to
  `~/.claude/skills/gusto-research/references/scientific-evidence.md`.
  If a scene needs a claim that has no row, look the study up with
  `studies.py` and add the row, or cut the claim. Never cite from memory.
- **His voice, in Latin American Spanish.** Write what he would say, the
  way he says it: `references/voice.md`. Spoken lines, notes to the editor
  and on-screen text are in Spanish. Notes to Gustavo are in English.
- **His mottos and rules win.** Same as `/gusto-research`: advice that
  breaks `channel.md` or `rules.md` is dropped, or he disagrees with it on
  camera. Rules are said in their **Regla** wording, with their
  **En pantalla** label.
- **Show, don't tell.** Something changes on screen every 30–60 seconds:
  an outfit change, a side-by-side, a B-roll cut or on-screen text.
- **Storyboard images start from the research.** Every outfit frame rests
  on at least one original image found in the research, saved untouched in
  `refs/` with its source in `refs/sources.json`. Generative AI only puts
  Gustavo into that outfit, in his own set. Originals are private
  references. Any original that should appear in the published video is
  flagged in the edit note "(derechos: verificar)".
- **Ask before spending.** Image generation costs money. Say how many
  images and which model, then wait for his go-ahead. After that, regenerate
  only the frames he asks for.
- **Never send a viewer to a video he hasn't cleared.** Links and the `cta`
  are `[k]` videos from `catalogue-review.md`. An unreviewed one stays
  marked "(unreviewed)" in the English notes.
- **Nothing is published or posted anywhere.** Write only to the home
  folder. Never print or ask in chat for API keys. They live in
  `$GUSTO_HOME/secrets/`.

## Files

Home folder: `$GUSTO_HOME`, else `~/.gusto-clasico/`. It is shared with
`/gusto-research` and described in
`~/.claude/skills/gusto-research/references/home-folder.md`. This skill
adds:

- `self/`: the self pack, his face, body and set.
- `productions/<idea file name without .md>/`: one folder per video.
  Format: `references/production.md`.

Scripts, run with `python3`. `--help` explains each one:

- `~/.claude/skills/gusto-script/scripts/media.py`: video frames, and the
  images on a web page.
- `~/.claude/skills/gusto-script/scripts/storyboard.py`: checks, generates
  and renders the storyboard.
- `/gusto-research`'s `transcript.py`, `comments.py`, `market.py` and
  `studies.py`, in `~/.claude/skills/gusto-research/scripts/`.

They need `yt-dlp` and `ffmpeg` on the PATH (`brew install yt-dlp ffmpeg`).

## 1. Load

1. Read the idea file in full. Read `channel.md`, `rules.md`,
   `learnings.md` and `catalogue-review.md`, and check that
   `self/self.json` exists. If the self pack is missing, build it first
   (§ Self pack).
2. Create `productions/<slug>/` with `refs/` and `storyboard/` inside.
   If the folder already has `guion.md`, this is a revision: § 6.
3. Find the target length. Use what the idea or his notes say. Otherwise:
   - grow and loyal: 8–12 minutes (the channel median is about 8);
   - interact: up to 18 minutes, like P_WG0WQGoUM;
   - Shorts: under 60 seconds each.

## 2. Research the topic in depth

The idea had an hour of research behind it. The script gets the full
picture. Write every finding to `research.md` as you go
(`references/production.md` § research.md), each with its URL or video ID
and the date.

1. **What he already said.** Run `transcript.py` on every old video on
   this topic, on every `links_to` and on the `cta`. Note:
   - what he said, with its timestamp, so callbacks quote him exactly;
   - where he has changed his mind;
   - the exact moment each link fits.
   Never contradict an old video by accident. When he has changed his
   mind, say so on camera.
2. **What his audience says.** Run `comments.py --ids <those videos>`. Read
   the comments on this topic: questions nobody answered, objections,
   words viewers use for things. Quote the best ones, with the author.
3. **The competition.** Run `market.py search` on the idea's main search
   phrases. Take the top 5 videos, and `transcript.py` the top 3.
   - What do they all cover? He covers it too, better.
   - What do they miss or get wrong? That is his edge.
   - What hooks do they open with?
   Never copy a structure, line or example.
4. **The experts.** Read at least three full articles from
   `~/.claude/skills/gusto-research/references/sources.md` on the topic
   (WebSearch, then WebFetch). The idea's own sources come first. Take the
   specifics: garments, fabrics, colours, measurements, names, history.
   Where they disagree with his mottos, it goes in the script as
   "X dice…, yo prefiero…".
5. **The science.** Re-check every row in the idea's
   `## Evidencia científica` with `studies.py check <id> --abstract`.
   Look up every new body claim the script will need. Update the
   table with the date you verified it.
6. **The rules.** For each rule in `rules:`, copy its **Regla** and
   **En pantalla** wording word for word. Flag rules still in `borrador`,
   and any open **Nota para Gustavo** that the script depends on.
7. **The images.** For every outfit, side-by-side and example, find the
   original images (§ 4). Collect them now, while the sources are open.
8. **Local facts.** Season and weather in Mexico when the video comes out.
   Where a viewer in Mexico can buy each core piece, with a price range,
   only if the script names prices. Brands as examples, never as sponsors
   unless he says so.

End with § Lo que cambió: what the deeper research changed in the idea
(beats added, cut or reordered; links swapped; claims narrowed) and the
new confidence, 1–3.

## 3. Write the script

Write `guion.md` in the format of `references/production.md` § guion.md.

1. **Structure first.** Outline the scenes with timings, and check the
   outline against these:
   - **Gancho (0:00–0:15):** show the payoff or the problem; no greeting.
   - **Promesa (by 0:30):** what the viewer gets and why stay to the end
     (an open loop that closes in the last scene). Then his short intro
     for new viewers.
   - **Beats:** the idea's `## Puntos clave`, refined by the research.
     Each one: the point, the visual proof, the rule, the link moment
     if there is one.
   - **Cierre:** close the open loop, then the `cta` in the last 20
     seconds over the end screen, then the sign-off "mantente siempre
     simple y clásico".
2. **Then the words.** Write every line Gustavo says, in his voice
   (`references/voice.md`). Under each scene, list the storyboard frames,
   the on-screen text, the edit notes (cut, transition, music, sound
   effect, B-roll, zoom) and the source of every fact.
3. **Length check.** Count the spoken words: about 150 a minute. Trim to
   the target.
4. **Shorts.** Mark 4–5 moments that stand alone in under 60 seconds,
   each with its first line and the scenes it uses. Prefer the idea's
   `## Shorts`, adjusted to the script.
5. **Outfits table.** List each outfit piece by piece. Give its original
   reference file in `refs/`, mark it core or trend, and list the frames
   that use it.
6. **Recording plan** (English): the takes grouped by setup (talking head,
   wide shot, black outfit for the AI swap), pick-ups, props, and the
   B-roll he must shoot or source.

## 4. Build the storyboard

1. **Plan the frames.** Write `storyboard.json`
   (`references/production.md` § storyboard.json). Plan about one frame
   per shot change: 15–30 for a 10-minute video. Each frame is one of:
   - `gen`: Gustavo in an outfit, generated from the self pack plus the
     originals. Use it for outfit reveals and side-by-sides.
   - `self`: him as he records, black outfit, talking head or wide shot.
     It uses a self-pack image as it is, with no generation.
   - `ref`: an original as it is: a B-roll example, an old video's frame,
     a garment close-up.
   - `card`: a text card or a graphic, for the rule labels and lists.
2. **Collect the originals.** For each `gen` and `ref` frame:
   - `media.py page <article URL>` lists the article's images;
   - `media.py get <image URL> --page <article URL> --out <production>/refs --name <frame>-<what>`
     saves one image;
   - `media.py frames <video id> --at <time> --out <production>/refs --name <what>`
     grabs a still from his old video or a competitor's.
   Look at each image before using it (Read it). The garment must match
   the script: colour, fabric, cut. If no page shows it, search further.
   Don't fall back on an image that doesn't match.
3. **Check, ask, generate.**
   - Run `storyboard.py check <production>`. Fix whatever it reports.
   - Run `storyboard.py gen <production> --dry-run` and read the prompts.
   - Tell him the number of images and the model. Generate when he
     agrees: `storyboard.py gen <production>`.
   - Look at every generated image (Read it). Check that it is him, the
     outfit is the one in the original, the set is his, and there is no
     text. Regenerate a frame that fails, once, with a sharper prompt.
     After that, mark it in the English notes rather than spending more.
4. **Render.** Run `storyboard.py html <production>`; `gen` does it too.
   It writes `storyboard.html`.

No image API key: say so once, write the storyboard with `self`, `ref`
and `card` frames, leave the `gen` frames pending, and point him to
§ Image API.

## 5. Present

In chat, in English:

1. One line: the title, the length, the number of scenes and frames, and
   the file paths: `guion.md`, `storyboard.html`, `research.md`.
2. What the deeper research changed, in three bullets at most.
3. The hook as he will say it, in Spanish, quoted.
4. Decisions he must make before recording: open rule notes, claims to
   confirm, unreviewed links, frames that didn't generate well.
5. Ask for his notes, or his approval.

When he approves, set `guion.md` to `status: aprobado` and the idea to
`status: scripted`. Mention in one line that the next step is
preproduction.

## 6. Revise

When the production folder already exists, read `guion.md`, `research.md`
and `storyboard.json`, then apply his notes:

- Change only what the notes touch. Keep the scene numbers and frame
  IDs stable, so his comments still point at the right place.
- If a change adds a claim or an outfit, research it the same way as in
  § 2, and record it in `research.md`.
- Regenerate only the frames whose prompt, refs or outfit changed:
  `storyboard.py gen <production> <ids> --force`. The old images move
  to `storyboard/old/`.
- Add a dated line under `## Cambios` in `guion.md`.

## Self pack

The generator needs pictures of Gustavo and his set: `$GUSTO_HOME/self/`,
with `self.json` mapping each role to its images (the first is the best):

| Role | What |
|---|---|
| `face` | Close, front-on, clear light, no caption over it. A 3/4 view is a good second. |
| `body` | Head to toe, natural stance. Shows his build. |
| `set` | His talking-head framing: the living room with the mirror, the lamp and the stairs. |
| `set-wide` | The wide shot of the same room, where he shows full outfits. |

`self.json` also holds a one-paragraph `description` of him and the set,
which goes into every prompt.

To rebuild it (`self`, or when he records in a new place):

1. `media.py frames <video id> --every 20 --out ~/.gusto-clasico/self/frames`
   on the video he names. Use 0RkvOeoZX78 by default.
2. Look at the stills. To see them all at once, tile them:
   `ffmpeg -pattern_type glob -i '<dir>/*.jpg' -vf "scale=480:-1,tile=5x5" -frames:v 1 /tmp/sheet.jpg`.
3. Pick the best still for each role. Grab sharper ones near a good moment
   with `--at`. Copy them to `self/<role>.jpg`, and update `self.json`.
4. Show him the picks and ask if they are right.

## Image API

`storyboard.py` uses Gemini's image models by default, or OpenAI's
`gpt-image` models. The key is read from `GEMINI_API_KEY` or
`OPENAI_API_KEY`, else from a file in `secrets/`. Walk him through it:

1. Gemini: on aistudio.google.com, choose **Get API key** and create one
   in a project with billing on. (OpenAI: platform.openai.com → API keys.)
2. Have him save it himself, never paste it in chat:
   `pbpaste > ~/.gusto-clasico/secrets/gemini_api_key && chmod 600 ~/.gusto-clasico/secrets/gemini_api_key`
   (or `openai_api_key`).
3. Run `storyboard.py models` to confirm the key works and list the image
   models. The first one listed is the default. To pin another, use
   `--model` or `GUSTO_IMAGE_MODEL`.

Images are billed per image. Check the provider's price page before a
big batch.
