# The rulebook

Gustavo grounds his style advice in a small set of timeless rules: fit, colour,
proportion, wardrobe. Repeating the same rules, in the same words and with the
same visuals, keeps his advice consistent and gives the channel its identity.
The rules live in `$GUSTO_HOME/rules.md`. They are his, so they stay outside
this repo.

## Format

One `###` heading per rule: the Spanish name, then a stable ID in brackets,
`[ajuste]`. The ID never changes once an idea uses it. Under the heading:

- **Regla:** the rule as it is said on camera.
- **Por qué:** the principle behind it.
- **En pantalla:** the short label and the recurring visual.
- **Explicada en:** the videos where he taught it.
- **Estado:** `borrador` or `confirmada`.
- **Nota para Gustavo:** optional; an open question.

## How a style idea uses it

- **Anchor.** Every style idea names one to three rules in its `rules:`
  frontmatter and in `## Reglas`. For each rule, it says how the video
  applies it and at which beat.
- **Same words.** The script quotes the rule's **Regla** line, or a close
  paraphrase that keeps its name, and uses its **En pantalla** label and
  visual. Viewers should recognise the rule from earlier videos.
- **Link back.** A rule's best `[k]` video under **Explicada en** is a natural
  `links_to`: "si quieres entender por qué, mira…".
- **No contradictions.** Advice that breaks a rule is either dropped or
  presented as a deliberate exception under `[reglas-guias]`, with the rule
  named. An expert who disagrees goes under `## Experto vs. Gusto`.
- **Advice no rule covers.** First derive it from an existing rule. If it
  really is new, propose a new rule in the idea (`## Reglas`, marked
  "propuesta") and in the run summary. Add it to `rules.md` as `borrador`
  only once Gustavo agrees. Don't invent rules inside a video.
- **Drafts.** A `borrador` rule may anchor an idea, but the idea says
  "(borrador)" next to it, and the run summary lists the drafts still
  waiting for him.

## Ideas from the rulebook itself

- **Coverage.** Each run counts which rules the last 12 published videos
  used. A rule nobody has used in a year is a candidate.
- **Rules that need a video.** A rule whose videos under **Explicada en** are
  all `[o]`, unreviewed, or more than 5 years old needs a definitive new
  video. That video becomes its main **Explicada en** and its standard link.
- **Series.** "Las reglas de Gusto Clásico", one rule per part, is a ready
  loyal series. A broad rule such as fit or colour can also be a grow video
  ("La regla de oro del estilo").
