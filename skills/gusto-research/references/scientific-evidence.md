# Scientific evidence for health and fitness claims

A video that says something about the body can be approved (`status: chosen`)
only when every such claim cites a peer-reviewed study in a reputable journal
that was looked up, checked and read. This holds for every pillar: a style
video that says "un estudio demuestra que mostrar el antebrazo te hace más
atractivo" needs a study too.

## What counts as a claim

Anything about training, muscle, fat loss, nutrition, supplements, sleep,
hormones (testosterone, cortisol), skin, hair, posture, health, ageing or
attractiveness research. Also any title or hook that says "ciencia",
"estudios" or "comprobado".

Not a claim: Gustavo's own story told as his story ("así me recuperé yo").
It becomes a claim the moment it generalises ("correr te cura de…").

## What counts as a source

- **Yes:** a peer-reviewed article in a reputable journal, indexed in PubMed
  (MEDLINE). Examples: *Sports Medicine*, *British Journal of Sports
  Medicine*, *Medicine & Science in Sports & Exercise*, *Journal of Strength
  and Conditioning Research*, *Journal of Applied Physiology*, *American
  Journal of Clinical Nutrition*, *Journal of the International Society of
  Sports Nutrition*, *Sleep*, *JAMA*, *NEJM*, *The Lancet*, *BMJ*.
- **Only with a reason:** a peer-reviewed journal outside PubMed that
  `studies.py check` finds on Crossref. Write why it is reputable.
- **Never a citation, only a lead to the study behind it:** coaches and
  their videos (Nippard, Galpin, Attia), books, news articles, blogs, press
  releases, preprints, conference abstracts, Wikipedia, AI answers.
- **Never:** retracted articles, journals of unknown standing, animal or cell
  studies used for a claim about people.

## How strong the evidence must be

| On camera the claim is… | It needs |
|---|---|
| Causal or a recommendation ("dormir poco baja tu testosterona", "entrena cada músculo 2 veces por semana") | A systematic review or meta-analysis, **or** two independent randomized controlled trials in humans that agree. |
| An association ("los hombres que duermen menos suelen tener…") | One good observational study or better, and the script says "se asocia", never "causa". |
| A single finding ("un estudio de 2020 encontró…") | That one study, named on screen, and nothing stronger said. |

Prefer the newest systematic review that covers the claim. When a study is
older than about 15 years, check that a newer review has not overturned it.
Treat these with care, and say so in the idea file:
- small samples (under 20 people) or trials shorter than a few weeks;
- populations unlike the viewer (elite athletes, the elderly, people with a
  disease);
- industry-funded studies with no independent replication.

## How to verify

1. `studies.py search "<claim in English>"` finds candidates: reviews,
   meta-analyses and RCTs in humans. Use `--any-type` only when nothing
   stronger exists.
2. `studies.py check <PMID or DOI> --abstract` confirms the article exists
   and is not retracted, and shows its journal, year and publication type.
3. Read the abstract. The study must say what the claim says: same
   direction, same population, and an effect big enough to matter to a
   viewer. If it says less, narrow the claim.
4. Never cite from memory or from another source's citation. Look every
   study up.

## In the idea file

`## Evidencia científica` holds one row per claim:

| Afirmación (como se dirá) | Estudio | PMID / DOI | Tipo | Qué encontró | Verificado |
|---|---|---|---|---|---|
| Entrenar cada músculo 2 veces por semana da más hipertrofia que 1 | Schoenfeld BJ et al., *Sports Medicine*, 2016 | PMID 27102172 | Meta-analysis | … in one sentence, with the population | 2026-10-29 |

The idea passes when every claim in `## Puntos clave`, the titles and the
hook has a verified row that is strong enough under the table above.

## On camera

- Say it with the strength the study supports, no stronger.
- Show the journal and year on screen when a study is quoted
  ("*Sports Medicine*, 2016"). It builds trust and suits his style.
- Medical topics (illness, medication, hormone therapy, hair-loss drugs) end
  with "consulta a tu médico". No diagnosing, no doses.
- The script and editing skills may not add a health claim that is not in
  this table. A new claim comes back here first.
