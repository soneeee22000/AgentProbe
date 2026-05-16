# AgentProbe — Research Publication Plan

Status: Draft v1 — Phase 0 (framing) complete. Phase 1 is the next executable step.

This document is the roadmap for turning AgentProbe from an engineering tool into a
peer-reviewed research contribution. It is grounded in the current codebase, not
aspiration: every claim below was checked against source files.

---

## 1. Thesis

> ReAct agents fail in structured, recurring, *model-specific* ways. We contribute
> (a) an empirically validated taxonomy of agent failure modes, (b) a benchmark
> designed to elicit those failures, (c) automated detectors for every failure
> mode with measured precision/recall, and (d) a large-scale study of where and
> why agents fail across models and providers.

The artifact (AgentProbe) is *infrastructure*, not the contribution. The
contribution is the taxonomy + benchmark + dataset + findings.

## 2. Honest assessment of the current state

What exists today (verified against source):

- **ReAct orchestrator** — `backend/src/agentprobe/application/services/orchestrator.py`.
  A complete from-scratch ReAct loop with step-level persistence.
- **Failure taxonomy** — 8 categories in `domain/entities/step.py:19` (`FailureType`).
- **Failure detectors** — 7 of 8 types are detected inline in the orchestrator:
  `CONTEXT_OVERFLOW` (line 127), `EMPTY_RESPONSE` (lines 153/168),
  `MALFORMED_ACTION` (line 230), `HALLUCINATED_TOOL` (line 253),
  `REPEATED_ACTION` (line 254), `TOOL_EXECUTION_ERROR` (line 278),
  `MAX_STEPS_EXCEEDED` (line 304). `GOAL_DRIFT` has **no detector**.
- **Benchmark** — 52 generic cases in `backend/data/benchmark_cases.json`.
- **Eval/scoring** — `eval_harness.py`, `scoring.py` (keyword-overlap + Jaccard).
- **Multi-provider** — Groq, Ollama, OpenAI, Anthropic, Google.

The gaps that block publication:

| Gap | Why it blocks a paper |
|-----|----------------------|
| Taxonomy is *asserted*, not validated | Reviewers require empirical grounding (open coding + inter-annotator agreement). |
| `GOAL_DRIFT` has no detector | A taxonomy with an unmeasurable category is incomplete. |
| Detectors are shallow heuristics | `TOOL_EXECUTION_ERROR` is a `"[ERROR]"` substring match; `CONTEXT_OVERFLOW` is a char count. None have measured accuracy. |
| Benchmark is generic | 52 math/search cases ("What is 25*17?") do not stress agents or elicit failures. |
| Zero experimental results | No runs, no failure distributions, no findings are checked in. |
| Scoring uses only lexical overlap | No LLM-as-judge baseline, no semantic scoring. |

## 3. The contribution and target venue

**Framing:** a fused benchmark + empirical-study paper.

**Primary venue:** NeurIPS Datasets & Benchmarks track — built for artifact +
analysis papers, more accommodating than an ML main track.

**Backup venues, in order:**
1. EMNLP / ACL — main track or Findings (empirical failure study).
2. FSE / ICSE research track — agent *debugging* framed as an SE measurement study.
3. Agent-focused workshops (NeurIPS/ICLR) — recommended as the *first* submission
   to validate the idea and collect reviewer feedback before the full paper.
4. ACL/EMNLP System Demonstrations or FSE/ICSE Tool track — the observatory as a
   demo paper (lower prestige, fast, can run in parallel).

**Recommended sequence:** workshop paper first (~6-8 weeks), then expand into the
NeurIPS D&B submission.

## 4. Phase 1 — the next executable step: taxonomy validation

This is what we do first. It converts the asserted 8-category enum into a
defensible, empirically grounded taxonomy.

### 4.1 Build a pilot trace corpus
- Run a fixed task set across all 5 providers and ≥6 models.
- Target ~300-500 complete agent traces, persisted with full step detail.
- Use the existing `orchestrator.py` + `run_repository`; no new infra needed.

### 4.2 Open coding
- Two+ annotators independently label each *failed step* with a failure mode,
  starting from but not constrained to the current 8 categories.
- Allow new categories to emerge; allow the current ones to be split or merged.
- Candidate additions to probe for: tool-argument errors, premature
  termination, observation misreading, reasoning-action mismatch.

### 4.3 Measure agreement
- Compute Cohen's / Fleiss' κ between annotators.
- Target κ ≥ 0.7. If lower, refine category definitions and re-code.
- Adjudicate disagreements to produce a gold-labeled set.

### 4.4 Output of Phase 1
- A revised, versioned taxonomy with a written definition + positive/negative
  examples for each category.
- A gold-labeled trace set — the ground truth for evaluating detectors in Phase 2.
- This becomes Section 3 ("The Failure Taxonomy") of the paper.

**Deliverable:** `docs/taxonomy.md` + a labeled dataset under `backend/data/`.

## 5. Full roadmap (after Phase 1)

- **Phase 2 — Complete & measured detectors.** Implement a `GOAL_DRIFT` detector
  (semantic similarity between current action and original query) and harden the
  existing 7. Evaluate each against the Phase 1 gold labels; report precision /
  recall / F1. Add an LLM-as-judge baseline for comparison.
- **Phase 3 — AgentProbe-Bench.** Replace the 52 generic cases with tasks
  *designed* to elicit failures: adversarial tool sets (hallucination), ambiguous
  goals (drift), long-horizon tasks (context overflow), distractor tools (repeated
  action). Document the design rationale per task.
- **Phase 4 — Large-scale study.** Full matrix: ≥6 models × 5 providers × the new
  benchmark, multiple seeds. Add cost/token tracking (currently absent). Release
  the full trace dataset.
- **Phase 5 — Analysis.** Failure-distribution heatmaps by model and category;
  statistical tests for model-specific failure signatures; cascading-failure
  analysis; correlation of failure modes with task properties.
- **Phase 6 — Write & release.** Paper + public dataset + leaderboard +
  reproducible harness. The clean codebase becomes a reproducibility asset.

## 6. Paper outline

1. **Abstract**
2. **Introduction** — agents fail silently; observability is unsolved; our contributions.
3. **Related Work** — ReAct (Yao et al. 2022), agent benchmarks, LLM evaluation, failure analysis.
4. **The Failure Taxonomy** — derivation, open coding, inter-annotator agreement (Phase 1).
5. **AgentProbe-Bench** — benchmark design, failure-eliciting task construction (Phase 3).
6. **Automated Failure Detection** — detectors + precision/recall vs. gold labels (Phase 2).
7. **Experimental Setup** — models, providers, matrix, metrics (Phase 4).
8. **Results** — failure distributions, model-specific signatures, cascading failures (Phase 5).
9. **Discussion** — what makes agents brittle; implications for agent design.
10. **Limitations** — single agent pattern (ReAct), lexical scoring, English-only.
11. **Conclusion** + artifact release.

## 7. Key risks

- **Weak findings.** If failures are uniform across models, there is no story.
  Mitigation: Phase 3 benchmark is explicitly designed to surface differences.
- **Low annotator agreement.** Mitigation: iterate category definitions in Phase 1.
- **Scope creep.** Mitigation: ReAct only; defer multi-agent and other patterns.
- **Compute cost.** Mitigation: free-tier providers + small models for the pilot.

## 8. Immediate next action

Begin Phase 1.2 instrumentation: a reproducible pilot-run script that executes a
fixed task set across all configured models and exports labeling-ready traces
(one row per failed step). This produces the corpus the human coding works on.
