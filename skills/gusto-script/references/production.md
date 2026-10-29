# The production folder

One folder per video: `$GUSTO_HOME/productions/<slug>/`. `<slug>` is the
idea's file name without `.md`, e.g. `2026-10-29-la-regla-de-oro-del-estilo-el-ajuste`.
This skill creates it. Preproduction and editing work in the same folder,
so this format is a contract: change it only together with them.

| Path | What |
|---|---|
| `research.md` | The deep research on the topic, with sources. |
| `guion.md` | The script. |
| `storyboard.json` | The frames, in order. `storyboard.py` reads it. |
| `storyboard.html` | The storyboard page, written by `storyboard.py`. |
| `storyboard/<id>.png` | Generated frames. `<id>.json` beside each one holds the model, the inputs and the prompt. Replaced versions go to `old/`. |
| `refs/` | The original images from the research, untouched. |
| `refs/sources.json` | Where each original came from: page, image URL, date. `media.py` writes it. |

## research.md

Spanish quotes and terms stay as they are; the notes are in English.

```markdown
---
idea: ideas/<slug>.md
updated: 2026-11-02
confidence: 3            # after the deep research, 1–3
---

# <title> — investigación

## Lo que ya dijo
Per old video: ID, title, year, what he said (quoted, with timestamp), where
he changed his mind, the moment it is linked from.

## Lo que pide el público
Comments on this topic: quote, author, video. Unanswered questions.

## Competencia
Top results for the search phrases: video ID, channel, views, age. For the
top 3 (transcribed): what they cover, what they miss or get wrong, their
hook. His edge, in one line.

## Expertos
Per article: URL, date, the specifics taken (garments, measurements, names,
history), and where it disagrees with his mottos.

## Ciencia
The re-verified table, in the same format as the idea's `## Evidencia
científica`, with today's verification date. New rows too.

## Reglas
Each rule: ID, **Regla** and **En pantalla** word for word, `borrador` or
`confirmada`, any open note.

## Datos locales
Season and weather, where to buy, price ranges (with URLs and dates).

## Lo que cambió
What the research changed in the idea, and why. The new confidence.
```

## guion.md

```markdown
---
idea: ideas/<slug>.md
title: "La regla de oro del estilo: el ajuste"
status: borrador        # borrador | aprobado
length: "9:40"          # estimated from the word count, ~150 words a minute
words: 1450
updated: 2026-11-02
---

# La regla de oro del estilo: el ajuste

## Para Gustavo
English. The promise in one line; the structure; decisions he must make
before recording; unreviewed links; claims and where they come from.

## Guion

### 1. Gancho (0:00–0:15)
**Cuadros:** 01, 02

**Gustavo:**
> ¿Qué pensarías si te dijera que esta camiseta de 200 pesos se ve mejor
> que este saco de 5 mil?

**En pantalla:** "La regla de oro: el ajuste"
**Edición:** corte seco al lado a lado en "5 mil"; zoom lento.
**Fuente:** rules.md [ajuste]

### 2. Promesa (0:15–0:35)
…

### 9. Cierre (9:10–9:40)
**Gustavo:**
> … Por el momento me despido, pero te recuerdo: mantente siempre simple
> y clásico.

**Edición:** pantalla final con <cta> a la derecha.

## Shorts
| # | Escenas | Primera línea | Duración |
|---|---|---|---|
| 1 | 3 | "La talla más grande NO te hace ver más delgado." | 40 s |

## Outfits
| Outfit | Prendas (prenda, color, tela, ajuste) | Base / tendencia | Original | Cuadros |
|---|---|---|---|---|
| 1 | Polo de punto azul marino en merino; jeans índigo rectos; botas chelsea de gamuza café | base | refs/03-polo-azul.jpg | 03, 04 |

## Grabación
English. Takes grouped by setup (talking head; wide shot; black outfit for
the AI swap), in recording order, with each take's scene numbers. Pick-ups,
props, B-roll to shoot or source.

## Fuentes
Every URL, video ID and study cited, with dates.

## Cambios
- 2026-11-03: shorter hook; frame 07 regenerated (his note: "the jacket is too long").
```

Rules for the script body:

- Scenes are numbered. Their numbers and the frame IDs never change in a
  revision. A new scene between 3 and 4 is `3b`.
- Every scene has **Gustavo** (or **Sin voz** for a B-roll montage) and
  **Cuadros**. Add **En pantalla**, **Edición** and **Fuente** whenever
  they apply.
- A link moment says which video, and what appears on screen: a card, or
  the old thumbnail.
- An original that would appear in the published video is marked
  "(derechos: verificar)" in **Edición**.

## storyboard.json

```json
{
  "title": "La regla de oro del estilo: el ajuste",
  "aspect": "16:9",
  "frames": [
    {
      "id": "01",
      "scene": 1,
      "time": "0:00",
      "kind": "gen",
      "shot": "plano medio, a cuadro",
      "self": ["face", "body", "set"],
      "refs": ["refs/01-camiseta-ajustada.jpg"],
      "prompt": "Gustavo in the white heavyweight T-shirt from the original, well fitted at the shoulders, facing camera, hands relaxed, confident half smile.",
      "line": "¿Qué pensarías si te dijera que esta camiseta…",
      "on_screen": "La regla de oro: el ajuste",
      "edit": "corte seco al cuadro 02 en \"5 mil\""
    },
    {"id": "02", "scene": 1, "time": "0:06", "kind": "ref", "refs": ["refs/02-saco-grande.jpg"],
     "line": "…se ve mejor que este saco de 5 mil?", "edit": "lado a lado con 01"},
    {"id": "03", "scene": 2, "time": "0:15", "kind": "self", "self": ["set"],
     "line": "Si recién me encuentras…"},
    {"id": "04", "scene": 3, "time": "0:40", "kind": "card", "on_screen": "1. El hombro"}
  ]
}
```

| Field | Meaning |
|---|---|
| `id` | Two digits, in order, stable across revisions. A frame inserted later is `05b`. |
| `scene` | The `guion.md` scene it belongs to. |
| `time` | Where it starts in the video, estimated. |
| `kind` | `gen`, `self`, `ref` or `card` (SKILL.md § 4). |
| `shot` | The framing: plano cerrado, plano medio, plano completo (cuerpo entero), detalle, lado a lado. |
| `self` | `gen`: the self-pack roles to send. Use `face` and `body`, plus `set` for the talking head or `set-wide` for full outfits. `self`: the one role to show. |
| `refs` | Originals in `refs/`. A `gen` frame needs at least one: the outfit or composition it copies. |
| `prompt` | `gen` only. In English. What he wears (as in the original), pose, expression, framing. Name the garments; don't describe his face, since the references carry it. |
| `line` | The words he says over this frame, from `guion.md`. |
| `on_screen` | On-screen text; the whole content of a `card`. |
| `edit` | The cut, transition, zoom, music or sound into or during this frame. |
| `aspect` | Optional, per frame: `9:16` for a Short's cover. |

For a side-by-side, make two `gen` frames (the "no" and the "sí") and say
in `edit` that they are cut together. A single image with two of him tends
to blur his face.
