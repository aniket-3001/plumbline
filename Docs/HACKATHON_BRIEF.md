# micro1 — Agentic Workflows Hackathon: Consolidated Brief

> Canonical reference compiled from `micro1 - First Hackathon97ce7c5.pdf` (10 pages), the
> rubric image (`image copy.png`), the use-case image (`image.png`), and the technology /
> qualification / rule-book notes supplied by the organiser.
> **Everything below is the organiser's requirement set, not our design.** Our design decisions
> live in the README and Improvement Changelog once the project starts.

---

## 1. The challenge in one line

> "Choose a problem worth solving and use agents to create something people would genuinely find useful."

Pick a **specific, meaningful problem you actually understand**. Use agents to solve it, and show
through **clear evidence** that your solution improves how the task is handled today.

Explain: who has the problem → what bottleneck they face → why solving it is valuable in practice.
The goal is something **a real person would want to use**.

### The four questions to keep in mind (they map to the rubric)

| # | Question |
|---|----------|
| 01 | Who has this problem? |
| 02 | What bottleneck makes it worth solving? |
| 03 | Does the agent solve it well? |
| 04 | Can another person reproduce the result? |

---

## 2. How agents can help (organiser's framing)

Use whichever agent capabilities genuinely help. The PDF names six levers:

1. **Better context** — feed the agent the right information.
2. **Better tools** — give it the right actions.
3. **Memory** — carry important information forward across steps/sessions.
4. **Verification** — catch errors before they reach the user.
5. **Specialised skills** — deepen ability in one particular task.
6. **Orchestration** — coordinate several agents.

> Judges focus on whether **each design choice improves the solution** and helps the agent reach the
> goal reliably. **Purposeful choices matter more than the number of components.**
> (i.e. do NOT bolt on a multi-agent swarm for show — every component must earn its place with evidence.)

---

## 3. Baseline requirement (mandatory for scoring)

Build a **simple baseline** representing a reasonable basic way to handle the task *before* your
solution. Acceptable baseline shapes given in the PDF:

- One direct prompt with basic instructions
- One general-purpose agent with basic tools
- A simple script or template
- The manual process people use today

Fairness rules:
- Baseline and final solution get the **same task and the same evaluation cases**.
- **Explain any meaningful difference in resources** available to each one.
- The final baseline-vs-solution comparison shows the **size** of the improvement;
  the changelog explains **where** the improvement came from. Both are needed.

---

## 4. Improvement Changelog (mandatory, clearly labelled)

A short changelog telling the story from baseline → final result. One entry **per important
experiment**, including experiments you **later removed** (and what removing them taught you).

Required columns:

| Stage | What you tried and why | Evidence | Decision / Learning |
|-------|------------------------|----------|---------------------|
| Baseline | Started with [basic approach] | [baseline result] | Established the starting point |
| Iteration 1 | Added a skill to address [issue] | [new result] | [kept / revised / removed] |
| Iteration 2 | Added verification after observing [failure] | [new result] | [kept / revised / removed] |
| Iteration 3 | Changed orchestration to improve [goal] | [new result] | [kept / revised / removed] |
| Final | Combined the changes that worked | [final result] | Identified the main contribution |

Rules: use the **same evaluation method** for every row so numbers are comparable; state what you
decided to do next; connect each entry to the evidence that guided the next decision.

---

## 5. Evaluation design

- Choose **one primary metric** that reflects what success means to the intended user
  (e.g. tests passing for a developer; time or cost saved for an ops team; calibration for forecasting).
- **Define what a good final result looks like *before* running the evaluation.**
- Same cases for baseline and final solution. **Publish complete results** — including failures.
- **Ten or more cases** is the target when the task allows it.
- Include **at least one deliberately challenging case** and explain what it revealed.
- You run the evaluation yourself. If the sample table fits poorly, **design your own scoring rubric
  and propose it** so judges can use it.

Sample table format:

| Metric | Simple baseline | Agent solution | Change |
|--------|-----------------|----------------|--------|
| Primary outcome | [value] | [value] | [change] |
| Human time per task | [value] | [value] | [change] |
| Cost per task | [value] | [value] | [change] |

---

## 6. Judging rubric — 100 points

| Criterion | Weight | What judges assess | Self-check question |
|-----------|--------|--------------------|---------------------|
| **Problem & user value** | **15** | Solves a meaningful problem for a clearly defined user. | Who experiences the bottleneck and why does solving it matter? |
| **Agent solution & engineering** | **30** | Uses agents purposefully and is technically sound. Context/tools may carry one project; memory, verification, skills or orchestration another. | Which design choices helped the agent solve the problem? |
| **End to end quality** | **20** | Completes a realistic, self-contained execution and produces a result the user can use — the finish of something a person would sign their name to, not an obvious AI-generated draft. | Would the intended user consider this high quality, or does it read as clearly AI generated? |
| **Measured improvement** | **15** | Demonstrates gains over a fair baseline; changelog connects each iteration to evidence. | Which changes truly improved the outcome? |
| **Reproducibility** | **15** | Another person has a clear path to run solution + baseline and reach the main result. | Could they do it from a clean environment? |
| **Hot take / insights** | **5** | Turns an observed failure mode into a practical lesson for building more reliable agents. | What did you learn and how would it change what you build next? |
| **Total** | **100** | | |

### Tie-break order (in this exact sequence)
1. Higher **Agent Solution & Engineering** score
2. Higher **Reproducibility** score
3. Higher **Measured Improvement** score
4. Higher **End to End Quality** score
5. Final panel review of documented evidence

Judges' decision is binding to the extent permitted by law and the official terms.

**Planning implication:** Agent Solution & Engineering (30) + Reproducibility (15) are also the
first two tie-breakers — they are worth more than their raw weight suggests. Optimise those first.

---

## 7. Qualification gate (pre-scoring, disqualifying)

A submission is **scored only after** it passes:

- **Eligibility**
- **Completeness**
- **Integrity**
- **Trace** checks
- **Reproducibility** checks

> A project that **cannot be run or verified may be disqualified before rubric scoring.**

**"What makes a submission valid?"** — timely, complete, original, policy compliant, and
reproducible, and it must include: the **repository**, an **archive**, **tests**, a **README**,
**agent-use evidence** (trajectories), and a **demo video**.

Checklist derived from that answer:

- [ ] Timely (submitted before deadline)
- [ ] Complete (all four deliverables present)
- [ ] Original
- [ ] Policy compliant
- [ ] Reproducible from a clean environment
- [ ] Repository
- [ ] Archive
- [ ] Tests
- [ ] README
- [ ] Agent-use evidence / trajectories
- [ ] Demo video

---

## 8. Final deliverables (four items)

### 01 — Complete solution code and improvement changelog
Share the full project and **everything required to run it, including the instructions that shape
each agent** (system prompts, agent definitions, skill files, tool specs).
The **README** must:
- introduce the **intended user**
- explain their **current bottleneck**
- describe **why solving it is valuable**
- contain a **clearly labelled Improvement Changelog**, one entry per meaningful iteration, each
  connected to the evidence that guided the next decision
- **close with the main failure mode and your hot take**

### 02 — Reproduction guide
Written for someone starting from a **clean environment**:
- setup walkthrough
- **exact commands** for: the solution, the baseline, and the evaluation
- which **data** is required
- what **output to expect**
- relevant **versions**, approximate **runtime** and **cost**

### 03 — Solution video (max 5 minutes)
1. The problem and the simple baseline
2. One realistic execution, start to finish
3. The final comparison
4. Brief walk through the changelog
5. **Highlight the change that contributed most**
6. **Highlight one experiment you removed**

### 04 — Agent trajectories
Representative trajectories for **every agent you used**, easy to follow from **agent instructions →
final result**. Each must show:
- what the agent did
- **how its tools responded**
- the **feedback that shaped its next step**
- any **retries**
- any **human checkpoints**

---

## 9. Ground rules (10)

1. You may build with tools and components you already know.
2. **Make it clear what existed before the competition and what you added.**
3. Use every tool and component according to its licence and service terms.
4. **Keep consequential actions controlled through a sandbox or simulation. Add human approval
   before the action happens.**
5. **Make a qualified human reviewer part of any solution that could significantly affect someone.**
6. Choose a legal and ethical use case that treats people and their data responsibly.
7. Use information you are allowed to share. **Public or synthetic data are usually easiest.**
   Approved anonymous data also works.
8. **Keep credentials and private information outside the submission.**
9. **Connect every claim about your results to the evidence you submit.**
10. Give judges enough access to run the project and reproduce the main result.

---

## 10. Technology policy

**Supported languages:** Python, TypeScript, Java, C++, Go, Rust.
Commonly used frameworks/libraries in those ecosystems are allowed **provided the entry stays
reproducible and complies with the final problem PDF.**

Illustrative (non-exhaustive) examples:

| Ecosystem | Named examples |
|-----------|----------------|
| Python | FastAPI, Flask, Django, LangGraph and related ecosystems |
| TypeScript | Node.js, Express, NestJS, Next.js |
| Java | Spring Boot |
| C++ | standard C++ and CMake toolchains |
| Go | Go modules, common Go web frameworks |
| Rust | Cargo, Tokio, Axum, Actix |

The problem PDF may prescribe a **starter repository, runtime, dependency limits, API access or
testing environment** where needed for fair and deterministic judging.

---

## 11. Example use cases (from the organiser's slide)

Engineering / Science · Forecasting · Game dev · Video and image generation · Office work ·
Professional work · Finance / Trading · Recruiting / HR · Legal / compliance documents ·
Web scraping / Research · E-commerce / Customer support · **+ more**

---

## 12. Three worked reference examples (Appendix of the PDF)

### A. Code analysis — "is this repository actually good?"
- **Who:** a team considering the purchase of a private repository; they need to know what the code
  is worth before agreeing a fair price.
- **Bottleneck:** a README or working demo reveals little about actual code quality. The buyer must
  understand an unfamiliar codebase, run build and tests, inspect architecture and dependencies, and
  assess technical debt and maintenance risk. Evidence also sits in PRs and open issues, and
  reviewers interpret the same signals differently. Without a repeatable method, valuation depends
  on incomplete or inconsistent judgment.
- **Agent:** analyse the repo and give a clear quality assessment before price negotiation. The team
  still has to define what "good" means and how quality should influence the valuation.
- **Evaluation idea:** have qualified reviewers rank ten approved codebases with a shared rubric;
  give the same codebases and rubric to the agent and to a simple baseline. Does the agent come
  closer to the reviewers' order, and can it justify each position with evidence?
- **Reproducibility:** approved repositories, exact setup/commands/tool versions/expected output for
  both baseline and agent; every score tied to a file, test result or build output.

### B. Candidate evaluation — "should we hire this person?"
- **Who:** recruiters and hiring managers deciding whether a candidate fits a role. Evidence is
  spread across the job description, target profile, CV, interview records and assessments.
- **Bottleneck:** reviewing each source in isolation makes it easy to miss contradictions or
  overweight one signal. A candidate can look perfect while the evidence doesn't line up. Suspected
  cheating makes the decision more sensitive because a warning sign alone is not proof.
- **Agent:** bring the evidence into one review, connect job requirements to demonstrated skills,
  check stated experience against approved sources, explain discrepancies. The recommendation must
  make its **evidence and uncertainty visible** while **leaving the final decision to a qualified
  reviewer**.
- **Reproducibility:** approved or **synthetic** candidate cases so evaluation doesn't depend on
  private information. Run baseline and agent on the same cases, **including one candidate with
  conflicting signals**. Report every result including failures; trace each score or concern back to
  its source. A second reviewer should reproduce the assessment without big discrepancies.

### C. Podcast translation — "can every version still feel like the same show?"
- **Who:** podcast creators/teams responsible for how a show sounds in every language; each
  translated episode must stay consistent with the episodes before it.
- **Bottleneck:** context spans hours of audio, multiple speakers, earlier episodes and prior
  translation choices. One episode can sound fine in isolation while inconsistencies accumulate
  across a series — a speaker's name pronounced differently, a recurring phrase translated
  differently, a joke that loses meaning because an earlier reference was handled another way. Every
  sentence can be correct while the series stops feeling coherent.
- **Agent:** translate across episodes and languages while keeping speaker identity, pronunciation,
  recurring terms, tone and prior decisions consistent. Whether the output is transcripts, subtitles
  or dubbed audio, it should preserve meaning and timing while sounding natural in the target language.
- **Reproducibility:** define evaluation before running it. Fixed set of episodes and target
  languages, same inputs for baseline and agent, **including one case that depends on a recurring
  detail**. Each translation choice points back to source audio or approved material (show notes,
  glossary). Anyone can rerun and check.

**Common pattern across all three examples (worth copying):**
1. A defined user with a real, costly judgment call.
2. A rubric/definition of "good" agreed *before* evaluation.
3. ~10 approved or synthetic cases, **including one hard/conflicting case**.
4. Same cases for baseline and agent.
5. **Every score traced back to a concrete artefact** (file, test result, build output, source audio).
6. Final decision stays with a **qualified human** where the stakes are personal.

---

## 13. Working checklist for our submission

**Design**
- [ ] One clearly named intended user, one bottleneck, stated value
- [ ] Each agent component justified by evidence, not by count
- [ ] Human approval gate before any consequential action; sandbox/simulation for side effects
- [ ] Qualified human reviewer in the loop if people are affected
- [ ] Public or synthetic data only; no credentials in the repo

**Evidence**
- [ ] >=10 evaluation cases, >=1 deliberately hard case
- [ ] Metric + "what good looks like" defined before running
- [ ] Identical cases for baseline and solution; resource differences documented
- [ ] Complete results published, failures included
- [ ] Every claim links to an artefact in the submission

**Deliverables**
- [ ] Repo + archive + tests + README (user, bottleneck, value, changelog, failure mode, hot take)
- [ ] Agent instruction files shipped (system prompts / skills / tool definitions)
- [ ] Reproduction guide: clean-env setup, exact commands (solution, baseline, eval), data, expected
      output, versions, runtime, cost
- [ ] Video <=5 min covering problem -> baseline -> one full execution -> comparison -> changelog ->
      biggest contributor -> one removed experiment
- [ ] Trajectories for **every** agent, incl. tool responses, feedback loops, retries, human checkpoints
- [ ] "What existed before the competition vs. what we added" stated explicitly

---

## 14. Source files in this directory

| File | What it is |
|------|-----------|
| `micro1 - First Hackathon97ce7c5.pdf` | Official 10-page brief (challenge, agent levers, baseline, changelog, evaluation, rubric, ground rules, deliverables, 3 appendix examples) |
| `image copy.png` | Rubric table with percentage weights (matches PDF p.5 point values) |
| `image.png` | "Example use cases" slide |
| `HACKATHON_BRIEF.md` | This consolidated reference |
