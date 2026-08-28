# Candidate Problem Statements — evidence-backed evaluation

Companion to `HACKATHON_BRIEF.md`.

**Revision history**
- v1 (2026-08-28): initial scoring. **Innovation scores were invented — no prior-art search was
  run.** Several "Problem & user value" scores rested on statistics quoted from memory.
- v2 (2026-08-28): prior-art check on A and E only. Both corrected 9->4 and 8->4.
- **v3 (2026-08-28, this version): full prior-art and prevalence check on all nine. Every
  Innovation score revised. Every prevalence statistic sourced or removed. Also corrects the
  "white space" claim made in v2, which was itself wrong.**

---

## What was verified vs. what is still judgment

| Dimension | Status |
|---|---|
| **Innovation** | ✅ Verified by search for all 9. Was fabricated in v1 |
| **Problem & user value** | ✅ Prevalence statistics now sourced to primary literature |
| **Audience** | ⚠️ Partially — informed by prevalence data, still an estimate |
| **Buildable** | ⚠️ Partially — existence of benchmarks/corpora verified; effort is judgment |
| **Reproducibility** | ❌ Judgment. Architectural reasoning (network dependency, determinism). Defensible |
| **Engineering depth** | ❌ Judgment. Subjective |
| **End-to-end quality** | ❌ Judgment. Subjective |

---

## Corrected summary table

| # | Idea | Rubric | Rules | **Innov (v1 -> v3)** | Pitch | Aud | Build |
|---|------|--------|-------|-------|-------|-----|-------|
| **A** | Proof-carrying security triage | 92 | 10 | ~~9~~ → **2** | 9 | 9 | 8 |
| **E** | SQL rewrite, dual oracle | 91 | 9 | ~~8~~ → **3** | 9 | 9 | 9 |
| **B** | Flake killer | 90 | 9 | ~~7~~ → **2** | 8 | 8 | 10 |
| **C** | Migration w/ self-built oracle | 88 | 9 | ~~7~~ → **2** | 7 | 8 | 9 |
| **F** | Spreadsheet auditor | 88 | 9 | ~~8~~ → **5** | 10 | 10 | 8 |
| **I** | Accessibility remediation | 86 | 10 | ~~7~~ → **2** | 9 | 9 | 8 |
| **D** | Dependabot finisher | 85 | 9 | ~~5~~ → **2** | 10 | 10 | 9 |
| **H** | Terraform blast radius | 84 | 10 | ~~7~~ → **4** | 8 | 7 | 7 |
| **G** | Repo resurrection | 84 | 8 | ~~8~~ → **1** | 10 | 9 | 7 |

**Average innovation score fell from 7.4 to 2.6.** Rubric totals barely moved, because novelty is
not a rubric line. The v1 innovation column was the single least reliable thing in the document.

---

## Correction to the v2 "white space" claim

In v2 I wrote that the untouched white space was *"nobody has systematically studied the agent
gaming its own verifier."* **That is also wrong.** It is published in at least three domains:

- [TerraProbe](https://arxiv.org/pdf/2606.26590) — "Layered-Oracle Framework for Detecting
  **Deceptive Fixes** in LLM-Assisted Terraform." Literally the thesis.
- [Trustworthy user-side accessibility agents](https://arxiv.org/html/2608.24913) — notes that
  validating on a single automated checker is "a metric that's **easy to game**," and prescribes
  apply → audit → keep only if violations strictly decrease → else roll back.
- [WorkstreamBench](https://arxiv.org/pdf/2605.22664) — documents an agent populating spreadsheet
  columns with hardcoded values instead of formulas: numerically correct, externally computed,
  invisible to value-based verification.

So the reward-hacking angle is a known, named, actively researched problem. It is still a *true* and
worthwhile thing to build against — it is not an original contribution.

---

## Evidence per candidate

### A — Proof-carrying security triage · Innovation **2/10**

**Prior art — heavily crowded:**
[Invicti "Proof-Based Scanning"](https://www.invicti.com/features/proof-based-scanning) (trademarked
commercial, [claims 94% auto-confirmation at 99.98% accuracy](https://www.prnewswire.com/news-releases/new-invicti-research-reveals-proof-based-scanning-automatically-confirms-94-of-direct-impact-vulnerabilities-with-99-98-accuracy-301385889.html), self-reported) ·
[OpenAnt](https://arxiv.org/html/2606.19149v2) (near-identical: LLM discovery → adversarial exploit
reasoning → isolated Docker execution → `CONFIRMED/NOT_REPRODUCED/BLOCKED/INCONCLUSIVE`) ·
[SAST-Genius](https://arxiv.org/pdf/2509.15433) (Semgrep → dataflow → LLM validation → PoC; FPs
225→20, ~91% less triage time) · [DARPA AIxCC](https://www.darpa.mil/news/2025/aixcc-results)
(>$29M, 7 LLM cyber reasoning systems, **open-sourcing was a competition requirement**,
[archive](https://archive.aicyberchallenge.com/)) ·
[Datadog Bits AI](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives/) ·
[QASecClaw](https://arxiv.org/pdf/2605.01885)

**Prevalence — my v1 claim was cherry-picked.** I said "70–90% false positives." Verified range is
**30–91%**, and the spread is methodological: real-world code with ground-truth vulns lands at
76–91% ([Ghost Security 2025: 2,116 flagged → 180 real = 91% FP](https://www.pixee.ai/blog/sast-false-positives-reduction));
tuned tools in specific ecosystems land at 30–35% (Semgrep precision measured at 35.7%); NIST SATE
figures are 18–36%. The problem is real; my number was the top of the range stated as the range.

### B — Flake killer · Innovation **2/10**

**Prior art — crowded, including open source:**
[FlakyGuard](https://arxiv.org/abs/2511.14002) (industrial scale, dynamic call graph + LLM-guided
traversal) · NIODebugger (LLM agent, 3-phase, correct patches for 101/172 previously unknown flaky
tests across 20 OSS projects) · [FlakyDoctor](https://dl.acm.org/doi/pdf/10.1145/3650212.3680369)
(neurosymbolic; **non-LLM components contribute 12–31%** — LLMs alone insufficient) ·
[FlakyFix](https://arxiv.org/abs/2307.00012) (**open-source scripts + public labeled dataset**) ·
[NeuroFlake](https://arxiv.org/pdf/2605.11482) · HiFlaky · FlakyQ · plus non-LLM iFixFlakies,
iPFlakies, DexFix, WeFix, FlakeSync

**Prevalence — better evidenced than I claimed (v1 said only "burns weeks"):** Google — 16% of tests
show some flakiness; 84% of pass→fail transitions involve a flaky test; ~1.5% of all test executions
fail incorrectly; ~2% of company-wide coding time. Microsoft — 13% of CI failures are flaky; **30
minutes average developer time per investigation**. Peer-reviewed industrial case study — **2.5% of
total productive developer time** (1.1% investigating, 1.3% repairing). Atlassian — 150,000+
developer hours/year in the Jira backend alone. Slack — 56.76% of CI failures pre-remediation.
[Survey of 121 developers](https://arxiv.org/pdf/2203.00483): 58% deal with flaky tests monthly.
→ **Problem score raised 13 → 14.** Note: the widely circulated "$400K/year for a 50-person team"
and "15–30% of CI time" figures are vendor extrapolations, not measurements. Do not cite them.

### C — Migration with self-built oracle · Innovation **2/10**

**Prior art — the exact design is published:**
[AgentModernize](https://arxiv.org/html/2605.17535v1) (Behavioral Specification Graphs +
**Equivalence Validator** doing automated test generation and **differential trace analysis**, with
targeted correction loops on divergence) ·
[Agentic deterministic validation / "Locksmith Loop"](https://arxiv.org/html/2607.28271) (a
**"Parity Gate"** differential oracle; cites Mokav and DiffSpec as precedents) ·
[LegacyTranslate](https://arxiv.org/pdf/2603.14054) (Radboud + ING, deployed on a ~2.5M-line
PL/SQL→Java migration) · Google's published case study of 39 internal migrations (~50% time saved).
Characterization tests / golden masters are standard industry practice.

### D — Dependabot finisher · Innovation **2/10**

**Prior art — this is a named paper:**
[LLM Agents for Automated Dependency Upgrades](https://arxiv.org/abs/2510.03480) (ASEW 2025) — my
idea exactly, down to the architecture: Summary Agent, Control Agent, Code Agent, iterative
compilation and testing, **handover to a human**. ·
[Automatically Fixing Dependency Breaking Changes](https://dl.acm.org/doi/10.1145/3729366)
(FSE 2025) — uses the **BUMP** benchmark of reproducible Maven failures **from Dependabot PRs**.

**Useful finding:** FSE 2025 reports agentic repair success of only **23%** (vs 19% zero-shot).
The problem is real *and* largely unsolved — that is headroom, and BUMP is a ready-made benchmark.
→ **Reproducibility raised 12 → 13** (benchmark exists, no need to build a corpus).

### E — SQL rewrite, dual oracle · Innovation **3/10**

**Prior art:** [E3-Rewrite](https://arxiv.org/pdf/2508.09023) — **our exact dual oracle**: falls back
to executing queries and comparing outputs over sampled DB instances, equivalence reward only on
exact match; 94.8% equivalence ratio on TPC-H · [GenRewrite](https://arxiv.org/pdf/2403.09060)
(PACMMOD; 70% correct rewrites vs 51.8% baseline) ·
[LLM-R2](https://arxiv.org/abs/2404.12872) (VLDB 2025) · [QUITE](https://arxiv.org/pdf/2506.07675) ·
EverSQL commercially. Known open problem: **SQL equivalence is undecidable in general**; empirical
execution-based equivalence is the standard workaround — which is what we would do.

Slight uplift over the others: QUITE and GenRewrite openly criticise each other's methods (execution
overhead vs. verifier coverage), so the methodology is genuinely contested rather than settled.

### F — Spreadsheet auditor · Innovation **5/10** — *least crowded*

**Prior art — adjacent, but the audit angle was not found:**
[FoRepBench](https://arxiv.org/pdf/2508.11715) is Excel **formula repair** (synthetic faulty formula
generation, execution-based metrics) · [WorkstreamBench](https://arxiv.org/pdf/2605.22664) is
end-to-end **spreadsheet task execution** in finance (rubric built by 2 MBAs + 3 finance
professionals over 700+ hours) · an OpenReview benchmark covers **financial statement auditing**
against FASB standards. **Nothing found for: audit an existing operational model for latent errors.**
No open-source repo surfaced for LLM spreadsheet auditing.

**Prevalence — strong, peer-reviewed, and I had it roughly right:**
[Panko](http://panko.shidler.hawaii.edu/SSR/Mypapers/whatknow.htm) synthesised 7 field audits (88
operational spreadsheets): **94% contained errors**, weighted average **cell error rate 5.2%**.
Conservative modern-methodology figure: **≥86%**. Cell error rates range 0.4–6.9%. Grounded in
cognitive-error research showing 2–5% human error rates on comparable tasks.
*Caveat to carry:* Pryor notes auditor error and possible sample bias; Powell et al. dispute the
HM Customs 6.9% figure's definition of "issue." Older audits found only 24% — methodology-dependent.
→ **Problem score raised 14 → 15.** My v1 "88%" should be cited as **94% (Panko 2005)** or the
conservative **≥86%**.

### G — Repo resurrection · Innovation **1/10** — *most crowded on the list*

**Prior art — this is an entire subfield:**
[EnvBench](https://github.com/JetBrains-Research/EnvBench) (DL4C @ ICLR 2025; 329 Python + 665 JVM
repos; **best approach configures only 6.69% of Python / 29.47% of JVM**) · **Repo2Run** (first
agent for fully automated env config + executable Dockerfiles; **86% success** on 420 repos;
dual-environment design with rollback) · **ExecutionAgent** (50 projects, 14 languages; 33/50 test
suites executed; ~74 min and ~$0.16 per project) · SetupBench · EnConda-Bench · RepoLaunch ·
SetUpAgent · SWE-Factory · [PIPer](https://arxiv.org/pdf/2509.25455) ·
[DeployBench](https://arxiv.org/pdf/2606.05238) · [Multi-Docker-Eval](https://arxiv.org/html/2512.06915) ·
EvoConfig

Nine-plus systems and five-plus benchmarks. **Do not build this.**

### H — Terraform blast radius · Innovation **4/10** — *contains the one identified gap*

**Prior art:** [TerraRepair](https://arxiv.org/abs/2607.11390) (tool-grounded LLM agent for IaC
repair; evaluated on TerraGoat / KaiMonkey) · [TerraProbe](https://arxiv.org/pdf/2606.26590)
(layered-oracle detection of **deceptive fixes**) · [RIVA](https://arxiv.org/pdf/2603.02345)
(configuration drift detection) · LLM code-smell detection for Terraform (IEEE COMPSAC 2025)

**But a real gap was explicitly identified:** the literature targets *security misconfiguration
repair* (Checkov/Trivy findings). **Plan-output risk classification — parsing `terraform show -json`
to classify `delete`/`replace` actions by blast radius — is under-served: academic work covers
pre-apply static analysis, and destructive-change tooling is commercial rather than peer-reviewed.**
→ This is the only concrete, search-confirmed white space in the whole set. Audience is narrow.
TerraGoat and KaiMonkey exist as ready corpora → buildability helped.

### I — Accessibility remediation · Innovation **2/10**

**Prior art — crowded, and my intended hot take is already published:**
[AccessGuru](https://arxiv.org/html/2507.19549v1) · [A11YRepair](https://arxiv.org/pdf/2606.21926) ·
[CodeA11y](https://dl.acm.org/doi/10.1145/3706598.3713335) (CHI 2025, Correction Agent over axe
DevTools) · [empirical study of detection/remediation/cost](https://arxiv.org/pdf/2605.27716)
(three-layer detection/repair/validation, Playwright + axe-core v4.10.2) ·
[Angular SPA remediation](https://arxiv.org/html/2602.17887v1) ·
[WebAccessBench](https://conesible.de/wab/whitepaper_webaccessbench.pdf) ·
[trustworthy user-side agents](https://arxiv.org/html/2608.24913) — **which states the "gaming the
checker" critique I was going to make as my own insight.**

Known ceiling worth noting: all axe-core-based evaluation undercounts real barriers, especially
keyboard order, screen-reader announcements, and cognitive accessibility.

---

## Honest conclusion

**Novelty is not achievable in any of these nine.** Every one is an active research area with recent
papers, and most have open-source implementations. Chasing novelty here is the wrong optimisation —
and, importantly, **the rubric does not score it.** "Original" appears only in the integrity sense.

What the prior art gives us instead is genuinely valuable for *this* rubric:

1. **Credible baselines.** The brief demands a fair baseline. Reproducing a published method
   (SAST-Genius's LLM-triage-without-execution; zero-shot vs agentic in the FSE dependency paper)
   beats inventing a strawman, and makes the improvement claim far more defensible.
2. **Ready-made benchmarks.** BUMP (Dependabot failures), EnvBench, TerraGoat/KaiMonkey,
   OWASP Benchmark. Free reproducibility points.
3. **Published headroom.** Dependency repair sits at **23%**. Environment setup at **6.69%**.
   These are documented ceilings we can aim to beat, with a citation for the starting line.

**Where genuine originality remains available, ranked:**
- **F's audit angle** (Innovation 5) — formula *repair* and end-to-end *task execution* are covered;
  auditing an operational model for latent errors was not found. Best audience, best pitch, best
  end-to-end-quality ceiling, peer-reviewed prevalence data.
- **H's plan-risk classification** (Innovation 4) — the only search-confirmed gap, but narrow.
- Everything else: execute-well territory, not new-idea territory.

## Still unverified

Engineering depth, end-to-end quality, and reproducibility scores remain my judgment, not evidence.
They are architectural reasoning and should be treated as informed opinion.

---

# Batch 2 — "agent formalizes, engine decides" (2026-08-28)

New organizing thesis: the agent does not decide; it drives a formal or simulation engine, and the
engine delivers the verdict. Rarer in hackathons than "LLM writes code, tests check it," and the
oracle is the engine itself.

## Checked this round

| Idea | Verdict |
|---|---|
| Optimization autoformalization (NL to LP/MILP) | **Heavily prior-arted.** [OptiMUS 0.1-0.3](https://arxiv.org/pdf/2407.19633), [NL4Opt](https://arxiv.org/html/2403.01342) (NeurIPS 2022), Chain-of-Experts, OR-LLM-Agent, [ORLM/AutoOR](https://arxiv.org/html/2604.16804v1), [ORPilot](https://arxiv.org/pdf/2605.02728), LM4OPT, LinearizeLLM. **Sub-gap confirmed:** CP proper (MiniZinc, CP-SAT scheduling) is "comparatively underexplored" versus LP/MILP |
| Network change verification (Batfish) | **Prior-arted.** [Closed-loop LLM+Batfish+RL](https://link.springer.com/chapter/10.1007/978-981-92-3400-4_13), [NL firewall config](https://arxiv.org/pdf/2512.10789), [CORNETTO](https://arxiv.org/pdf/2604.22513), AskBatfish |
| Mutation-score test strengthening | **Prior-arted, including the headline finding.** [Meta ACH](https://arxiv.org/html/2501.12862v1) deployed on 10,795 classes across 7 platforms; TestGen-LLM covered 32% vs 5.3% of classes but killed 2.4% vs 15% of mutants. [MuTAP](https://www.sciencedirect.com/science/article/abs/pii/S0950584924000739), [MutGen](https://arxiv.org/abs/2506.02954) |
| Statistical error checking in papers | **Prior-arted.** [Preprints.ai](https://hahnel.substack.com/p/preprintsai-how-much-of-peer-review) already runs GRIM + statcheck + Benford + paper-mill detection |
| **Least-privilege for AI agents (SMT)** | **GAP CONFIRMED** |
| **Slicer-in-the-loop 3D design** | **GAP CONFIRMED** |

**Running total: 15 ideas prior-art-checked. 13 fully occupied, 2 with confirmed openings,
2 with partial sub-gaps (CP scheduling; Terraform plan-risk classification).**

---

## N1b — Least-privilege policies for AI agents, SMT-verified · Rubric **93**

**Pitch:** Your AI agent has admin credentials because nobody knows what it actually needs. We watch
what it does, derive the minimal policy, and **prove** the new policy is strictly less permissive
while every task still completes.

**Confirmed gap (quoted from search):** *"None of the results show a system that combines an LLM
agent's runtime behavior with Zelkova-style SMT refinement — the formal-methods line (Zelkova, ALPS,
PrivLess) targets serverless/cloud workloads, while the agent line (SkillScope, Agentic IAM) uses
probabilistic runtime-monitoring approaches rather than decision procedures. The intersection looks
like open research territory."*

**Dual oracle:** (1) [SMT decides policy containment](https://www.cs.utexas.edu/~hunt/FMCAD/FMCAD18/papers/paper3.pdf)
— is the new policy strictly less permissive? Decidable; this is what AWS Zelkova does.
(2) Replay the agent's task suite under the new policy — do all tasks still pass?

**Adjacent prior art (not blocking):** Zelkova / AWS CheckNoNewAccess and CheckAccessNotGranted ·
[SkillScope](https://arxiv.org/pdf/2605.05868) · [ALPS](https://arxiv.org/pdf/2603.25393) ·
Zouari "Toward Agentic IAM" (BDCAT 2025; 39-46% action reduction versus static roles) ·
AgentRaft (arXiv 2603.07557) · OWASP LLM top-10 "excessive agency"

**Hot take, handed to us by the literature:** *"SMT-verified least-privilege policies bound
authorization, not reachability."* Denied one path, the agent finds another route to the same effect.

| Rubric line | Score |
|---|---|
| Problem and user value | 14/15 — urgent and universal for anyone deploying agents in 2026 |
| Engineering | 28/30 — trace-based policy synthesis, SMT encoding, replay harness, over/under-privilege measurement |
| End-to-end quality | 17/20 — policy diff, proof, task-pass evidence |
| Measured improvement | 15/15 — permission reduction AND task pass rate, both mechanical |
| Reproducibility | 14/15 — LocalStack/moto offline, Z3 deterministic |
| Hot take | 5/5 |
| **Total** | **93** |

Personal criteria: Rules 10 · Innovation 7 · Pitch 9 · Audience 9 · Build 7

**Honest weaknesses:** agent-securing-agents can read as self-referential; the gap is an
*intersection of two literatures*, a weaker opening than untouched ground, and someone may be
writing that paper now; LocalStack/moto fidelity has limits; "permission reduction %" is soft on its
own — the defensible metric is reduction *while maintaining 100% task success*.

---

## N8 — Slicer-in-the-loop 3D design · Rubric **88**

**Pitch:** Describe the part you need. The agent designs it, and the slicer proves it will actually
print — manifold, no unsupported overhangs, no thin walls — before you waste nine hours of filament.

**Confirmed gap (quoted from search):** *"An explicit slicer-in-the-loop oracle — running
PrusaSlicer/CuraEngine headlessly to check manifoldness, overhang angles, unsupported islands, thin
walls, and estimated print time as a reward signal — appears underexplored."* Existing work verifies
either geometrically (render/CLI compile) or post-hoc
([camera monitoring mid-print](https://arxiv.org/pdf/2408.14307)).

**Adjacent prior art:** [AgentsCAD](https://arxiv.org/pdf/2607.02448) (Design Reasoner + CAD Code
Verifier agents) · [LLM-ADAM](https://arxiv.org/pdf/2605.03328) · FDM-Bench ·
[RocketBench](https://arxiv.org/pdf/2606.00097) (excellent template for simulation-in-the-loop
composite scoring) · OpenSCAD Pantheon benchmark · DesignBench

| Rubric line | Score |
|---|---|
| Problem and user value | 12/15 — real but lower stakes; wasted filament, not money at scale |
| Engineering | 25/30 — OpenSCAD generation, mesh analysis, slicer integration, overhang/support analysis |
| **End-to-end quality** | **19/20 — best artifact of any candidate. You hold the printed part** |
| Measured improvement | 14/15 — first-try print success rate, material waste |
| Reproducibility | 14/15 — headless slicer, deterministic, offline |
| Hot take | 4/5 — geometric reward hacking: agent makes the part solid or trivial to satisfy the slicer |
| **Total** | **88** |

Personal criteria: Rules 8 · Innovation 6 · Pitch 10 · **Audience 6** · Build 7

**Honest weakness:** lowest problem-value score in the batch and the narrowest audience. It wins on
demo quality, not on stakes. Best five-minute video of anything on either list.

---

## Rest of batch 2 — UNCHECKED, provisional

Based on this session's hit rate, assume roughly two-thirds have prior art not yet found. The
Innovation column here is especially unreliable.

| ID | Idea | Rubric | Rules | Innov | Pitch | Aud | Build |
|----|------|--------|-------|-------|-------|-----|-------|
| N34 | Agent red-teams another agent's tool policy (oracle: did the target take a forbidden action) | 88 | 9 | 5 | 8 | 8 | 8 |
| N2 | CP scheduling formalization — NL to MiniZinc/CP-SAT with infeasibility explanation | 87 | 9 | 6 | 9 | 9 | 7 |
| N39 | Reproducible-build agent — oracle is a byte-identical rebuild in a clean container | 87 | 8 | 4 | 8 | 8 | 7 |
| N31 | Benefits/tax eligibility checked against a reference implementation (OpenFisca) | 86 | 9 | 5 | 10 | 10 | 7 |
| N37 | Analog circuit design verified by ngspice against a spec | 86 | 8 | 6 | 8 | 5 | 6 |
| N36 | Document accessibility (PDF/UA via veraPDF) — less crowded than web a11y | 85 | 10 | 5 | 9 | 8 | 8 |
| N30 | Deterministic replay to make concurrency bugs reproducible every run | 85 | 8 | 4 | 7 | 5 | 5 |
| N32 | Cross-document contract consistency over time (memory-centric) | 84 | 9 | 5 | 8 | 7 | 8 |

## Standing across both batches

Highest rubric totals: **N1b 93** · **A 92** · **E 91** · **B 90** · **N8 88** · **N34 88** · **F 88**.

Only N1b and N8 have a confirmed novelty opening. **N1b is the first candidate to lead on rubric
score and relative originality simultaneously.**
