# What actually wins these hackathons — research notes (2026-08-28)

Companion to `HACKATHON_BRIEF.md` and `CANDIDATE_IDEAS.md`.

---

## 1. micro1's hackathon has no prior edition

The brief is filenamed `micro1 - First Hackathon97ce7c5.pdf`, and searching for micro1 hackathon
winners returns nothing but other companies' events. **Treat this as their first.** No past winners
to reverse-engineer, and no established house style — the rubric in the PDF is the only signal we
have about their taste, and it should be read literally.

---

## 2. Who the judges are — this is the most actionable finding

micro1 is not a generic sponsor. Their business *is* evaluation.

| Fact | Source |
|---|---|
| AI recruiting engine; "Zara" AI interviewer runs asynchronous technical interviews at scale | [micro1](https://www.micro1.ai/ai-interview-guide) |
| **3,000+ AI interviews per day**; 85% reduction in recruitment cost vs traditional | [Anthropic customer case study](https://www.anthropic.com/customers/micro1) |
| 1M+ AI-led interviews; ~1% of candidates pass screening | company statements |
| $35M Series A at **$500M valuation** (01 Advisors) | [TechCrunch, Sep 2025](https://techcrunch.com/2025/09/12/micro1-a-competitor-to-scale-ai-raises-funds-at-500m-valuation/) |
| Gross run rate **$100M → $500M in eight months** | [TechCrunch, Aug 2026](https://techcrunch.com/2026/08/20/ai-data-startup-micro1-reaches-500m-gross-run-rate-amid-ai-training-boom/) |
| Competes with **Scale AI, Mercor, Surge** — supplying expert human data and RL environments to AI labs | Sacra / TechCrunch |

**What this means.** These judges spend every working day on: how do you score a human reliably, how
do you know a grader is right, what is ground truth, how do you keep assessment consistent at
volume. They sell rubric quality to AI labs.

That explains why their rubric is abnormally evaluation-heavy for a hackathon — mandatory fair
baseline, same cases both arms, 10+ cases, one deliberately hard case, publish failures, changelog
tying each iteration to evidence, and a pre-scoring reproducibility gate. **This is not typical
hackathon judging. It is the rubric of a company that builds evaluation systems professionally.**

**Implication:** measurement rigour is not a box to tick here — it is the judges' home turf. A weak
or hand-wavy eval will be spotted instantly. Conversely, genuinely rigorous evaluation methodology
is the thing this specific panel is best equipped to appreciate, and most likely to reward.

**Caution:** their PDF's appendix example #2 is *"Candidate evaluation: should we hire this person?"*
— which is literally their own product. Building that means (a) building the example they handed
out, and (b) competing on a domain where the judges know more than we do. Avoid.

---

## 3. What has actually won adjacent hackathons

### Anthropic "Built with Opus 4.7" (Feb 2026) — domain experts swept it
Winners: **MedKit** (built by an Istanbul physician-turned-engineer, for a real clinic; four parallel
Claude Code sessions), **ARIA** (multi-agent industrial machine-alert analysis), **Wrench Board**
(visual AI over 80-page circuit board schematics for hardware repair), **Maieutic / MaestrIA**
(students must explain logic before unlocking the editor; digitising traditional carpentry knowledge).

> The top three prizes went to a doctor in Istanbul, a former microsoldering technician in the French
> Alps, and a computer science teacher in Chile — none from Silicon Valley.
> [Claude blog](https://claude.com/blog/meet-the-winners-of-built-with-opus-4-7-claude-code-hackathon) ·
> [EdTech Innovation Hub](https://www.edtechinnovationhub.com/news/a-doctor-a-carpenter-and-a-teacher-win-anthropics-global-opus-47-hackathon)

The **Opus 4.6** edition repeated the pattern: a personal injury lawyer, a cardiologist, a roads
infrastructure specialist, an electronic musician — and exactly one professional software engineer.

**Lesson: deep domain knowledge beats technical novelty.** None of these were research contributions.
All were known techniques applied to a domain the builder personally understood.

### Cerebral Valley x Anthropic (Feb 2026) — won on evaluation methodology
`everything-claude-code` won with **eval-driven development**: define pass/fail criteria *before*
building, capability vs regression eval templates, reliability via **pass@k / pass^k**, `baseline.json`
for regression tracking, CI integration with baseline checkpointing by SHA.

> Judges wanted submissions showing potential "beyond simple task completion"; what stood out was
> **"systematic quality, not just speed."**
> [claudeskills.info](https://claudeskills.info/blog/everything-claude-code-hackathon-eval-driven/)
> *(single-source; the 68k-star claim should be verified against GitHub before citing)*

### Covasant AI Hackathon 2025 (India) — winner was an agent *evaluation* tool
VIT Chennai won nationally with a system to **evaluate AI agents** via stress testing, safety checks
and cost diagnostics.
[source](https://news.careers360.com/vit-chennai-wins-covasant-ai-hackathon-2025-winners-rs-1-lakh-internship-students-competition)

### Others
- **Microsoft AI Agents Hackathon 2025** — 18,000 registrants, 570 submissions. Best Overall:
  *RiskWise*. Judged on innovation, impact, usability, solution quality, category alignment.
  [winners](https://microsoft.github.io/AI_Agents_Hackathon/winners/)
- **Kong Agentic AI 2025** — Best Solo went to an *Autonomous Security Auditor*.
  [source](https://konghq.com/blog/news/winners-of-kong-agentic-ai-hackathon)
- **Anthropic Opus 4.8 Build Day** (Jun 2026, SF) — 1,500 applied, 310 built in 12 hours.
  Winners: *Sim Francisco* (Census-seeded digital twin, poll a synthetic city), *Tekton* (building
  reconstruction), *Custom Universe* (synthetic environments for robotics training data).

---

## 4. What the judging literature says

From [JetBrains' notes from the judging table](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/),
[Devpost judges](https://info.devpost.com/blog/hackathon-judging-tips), and
[browser-use](https://browser-use.com/posts/how-to-win-hackathons):

- **Research across 48 hackathons found only a minority had clear objectives or a concrete plan for
  assessing success** — which is why flashy demos routinely beat useful solutions. Without deciding
  what winning means before the first demo, judges default to theatre: energy in the room, polished
  slides, cleanest story.
- The stated countermeasure is exactly micro1's rubric: separate scores for feasibility, impact and
  **evidence**, applied identically to every team.
- **"Judges are looking for evidence against a baseline — explicitly show before/after, current
  painful workflow versus yours, with a measurable delta. This directly answers the 'evidence'
  column that most teams leave blank."**
- The demo is the product. Visualise the winning demo, then build backwards toward it. Keep demo
  steps short and rehearsed; judges cannot absorb technical depth in a few minutes.
- Allow interactive input so judges can drive it themselves, not just watch a scripted path.

---

## 5. Implications for our shortlist

1. **Measurement rigour is the highest-leverage investment**, and unusually so with this panel. Two
   independent signals converge: micro1 sells evaluation for a living, and the most similar
   Anthropic hackathon was won by an eval methodology. Build the eval harness first, not last.
2. **Novelty continues to look irrelevant.** Not one winner found was a research contribution.
   Confirms the `CANDIDATE_IDEAS.md` v3 conclusion from a completely different angle.
3. **Domain grounding beats generic developer tooling.** A doctor's clinic tool and a technician's
   schematic reader beat general-purpose agent frameworks. Our A/B/C/D/E/G are all generic dev
   tools that judges will have seen versions of. **F is the only candidate on our list with a
   specific, non-technical domain and a real human user.**
4. **The demo has to be drivable.** Whatever we choose must produce something a judge can poke at
   live and immediately recognise as correct or incorrect.
5. **Do not build candidate evaluation / hiring.** It is their appendix example *and* their core
   product.

## Open question this raises

The strongest single predictor across the Anthropic hackathons is that the builder had **personal
domain expertise**. We have not yet established what domain Aniket actually knows deeply — that is
probably a more important input to the decision than any remaining rubric arithmetic.
