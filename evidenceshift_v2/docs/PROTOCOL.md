# EvidenceShift pilot protocol v1.0

Status: designed before any external model evaluation in this workspace. This is a local protocol freeze, not a registered preregistration. Independent human annotation is pending.

## Research question and claim boundary

Does an explicit evidence-checking instruction improve evidence-grounded decisions compared with a concise document-grounded baseline, holding model, packet, output schema, and generation parameters fixed?

This evaluates the generation stage of a RAG-like pipeline with supplied documents. It does not evaluate retrieval, open-web research, source authenticity, user decisions, real-world factual accuracy, or autonomous agents. All organisations and policies are fictional. Avoid calling this a novel solution to conflicting evidence: prior work already studies that question and prompting interventions.

## Design

Forty test cases in ten domain families, with four related cases per family: resolved discrepancies, unresolved conflicts, missing target information, and consistent controls. Eight development cases use two additional domain families. Development examples share construction patterns with test examples; this is domain separation, not a guarantee of generalisation to unseen mechanisms.

The ten resolved cases comprise two each of explicit supersession, future effective dates, draft authority, archive republication, and unofficial newer claims. The other categories use explicit labels to establish the intended answer. These deliberately legible packets may produce ceiling effects. Publish that limitation and inspect it in development; do not quietly make test cases harder after viewing test results.

Each case has two documents, four deterministically shuffled answer options, a status, and a private gold rationale. Document IDs and initial ordering are varied. All answers must include concise justification and exact quotations. Both conditions receive the same format requirements and evidence. Only the instruction differs. The longer treatment is a package intervention: this two-arm design cannot isolate length, individual instructions, or reasoning effort. A length-matched control and component ablations are future work.

Run each condition once in each of two document orders per case: 40 × 2 conditions × 2 orders = 160 scheduled test calls. A development run has 32 calls. Additional repeats must be selected before test execution and reported. Both conditions use identical settings; default parameters do not force temperature because some models do not support it. Record provider defaults when unspecified. Prefer a pinned model revision when available. Randomise execution order with seed 20261114. Each call is a fresh conversation. Document order is paired across conditions; answer-option order is fixed within a case.

## Primary outcome

Decision correctness is 1 only when the response meets the common output schema and both selected option and status match the gold labels. Otherwise it is 0. This is constrained-choice decision accuracy, not free-form factual accuracy. Because schema validity is required, also report schema compliance separately and inspect format failures. Do not describe this as pure reasoning ability.

The primary contrast is evidence_checks minus baseline. Average across orders and repeats within cases and then across four cases within each family. Families have equal weight. The implementation computes the equivalent mean over the balanced rows within each family. Report the mean of ten paired family differences and a percentile paired-family bootstrap interval (10,000 draws, seed 711). Only ten family clusters and shared templates make this an exploratory uncertainty summary. Repeats and order variants are not independent cases. No confirmatory hypothesis test or population-generalisation claim is planned.

## Secondary and diagnostic outcomes

- Exact-quote validity: proportion of supplied quotations that are verbatim substrings of the named document. This is not entailment.
- Gold evidence-set coverage: at least one annotated acceptable source set is covered by valid quotations. Mentioning any substring from the right source is insufficient to establish semantic support; report the limitation.
- Grounded-decision proxy: correct decision, all quotes valid, and evidence-set coverage. Label it as a proxy in every table.
- Category accuracy, valid-decision consistency under document reversal, schema failures, transport failures, finish reasons, latency, and reported token usage.
- Human semantic review: supported justification and absence of unsupported factual claims. These require blinded human annotations; no automatic semantic score is claimed.

Transport failures are retained as zero for the intention-to-evaluate primary outcome and counted separately. If outages dominate, label the run technically inconclusive. Never silently drop failures or select favourable retries. Retries apply only to transient transport errors, not to wrong or malformed model answers; all attempts may incur billing. Resume preserves completed failures. If a configuration change is necessary, create a new run and disclose the abandoned run. Analysis rejects incomplete schedules.

## Dataset review before final evaluation

Read every packet against its gold rationale and evidence sets. A human should record accepted/revised/rejected labels and reasons in data/review_checklist.csv. Another reviewer is preferable, but do not claim one exists unless they participated. The generated checklist begins pending. Revisions require a new dataset version and freeze. Do not edit labels after seeing test outputs without reporting an exploratory correction analysis and preserving the original result.

## Blinded output review

Export shuffled responses without condition labels, case category, or answer key. Keep the private review key from reviewers. Give reviewers the packet, response, and rubric. Stylistic differences may still reveal the condition, so blinding is imperfect. Score all responses if feasible. Have two reviewers independently annotate, record agreement before adjudication, and retain both original files. A single reviewer is acceptable for a pilot if explicitly disclosed; the script summarizes one complete annotation file at a time. No fabricated reviewer identities or ratings.

## Versioning and stopping

The freeze records hashes of code, datasets, prompts, and this protocol. Run manifests include the freeze, config without API secrets, planned jobs, model ID, Python version and time. Logs retain request hashes, response IDs, returned model metadata where provided, usage, and outputs. The request can be reconstructed from frozen inputs. Local hashes detect accidental edits; they do not authenticate a provider response or establish public preregistration.

Use development to verify API compatibility, budget and prompt clarity. Make any justified changes before freezing the final test version. Stop after the planned test schedule; do not add models or repeats because the result looks weak. Report inconclusive and negative results. Record any deviation in docs/DEVIATIONS.md before analysis when possible.

## Ethics and limitations

No personal data, medical advice, legal advice, financial decisions, or real institutional policies are used. Synthetic authority labels are trusted stipulations, not verified provenance. The evaluation cannot show resistance to forged authority, deceptive timestamps, document prompt injection, or long noisy retrieval contexts. Malicious actors could use findings to make misleading evidence appear authoritative. Human oversight and real-source authentication remain necessary outside the pilot.

AI assisted the code, synthetic data, protocol and drafts. The author must verify them, run the experiment, review evidence, and own the conclusions. Do not convert mock results into experimental findings. Do not submit the report scaffold as a completed empirical report.

## Amendment: Gemini execution and pacing (14 November 2026)

Before formal development or test evaluation, select Gemini 3.8 Flash via Google's OpenAI-compatible endpoint. Hold temperature at 0, reasoning effort low, max_tokens 4096 and JSON object output mode constant in both conditions. Use ten request starts per minute in one serial process; retries share the limiter. Honour Retry-After headers and Google RetryInfo delays, use exponential backoff with jitter, and do not retry earlier than a long provider cooldown. Pause after three consecutively failed jobs. These are local controls, not a guarantee against project-wide RPM, TPM or daily quotas. No condition-specific settings or model switching during a run.

Post-study engineering update: the current root runner propagates provider cooldowns to subsequent jobs and preserves their remaining duration on resume. A long cooldown pauses the run. The study implementation and protocol are retained in frozen_study; use that implementation to reproduce the delivered analysis. This change is not retroactively represented as having been used in the study.
