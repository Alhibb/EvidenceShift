# EvidenceShift challenge protocol version 2 candidate

Prepared 15 November 2026 after observing the first pilot's ceiling. This is a new study, not a revision of the completed pilot. No challenge model outputs have been observed. A local freeze is not public preregistration. Independent human label review remains pending.

## Question and comparison

When issue date, effective date, scope and authority interact, do targeted evidence checks improve decisions relative to a generic instruction of similar length?

Primary comparison: evidence_checks minus generic_control. Secondary comparison: evidence_checks minus baseline. All prompts use identical response-format instructions, context, model and generation settings. Word counts are reported. Similar word length is not identical tokenizer length, semantic complexity or compute. The comparison cannot isolate every prompt component.

## Cases and separation

24 test cases form 12 counterfactual pairs, with two pairs for each of six mechanisms: effective time, partial scope, authority, version history, unresolved conflict and missing information. Six development cases form three separate pairs. Every pair has the same question, options, source titles and source order; exactly one document's text changes and the correct answer changes. The changed fact determines the intended conclusion. Public case IDs are opaque; pair IDs and gold labels never enter model input. Options and document IDs are randomized once within each pair and held fixed across its variants.

All organisations, notices, dates and identifiers are invented for this study. No private user documents or external policies are included. The same AI assistant helped construct the first and second studies. AI consistency checks are not independent human validation. Development and test have different scenarios but share mechanisms; this does not establish out-of-distribution generalization. Test status distribution is 20 answer, 2 conflict and 2 insufficient, so abstention conclusions will be especially weak. Four constrained options also make the task easier than free-form extraction.

Packets encode priority rules explicitly but do not label a source as the winning answer. Cases require combining records. The intended increase in difficulty is a design hypothesis, not an empirical result. Do not call this benchmark harder in measured terms until actual model results support that description.

## Planned execution

Use gemini-3.8-flash, temperature 0, reasoning effort low, max_tokens 4096 and JSON-object mode, via the existing tested client. Three conditions and two document orders yield 144 test calls and 36 development calls at one repeat. Calls are serial at no more than ten starts per minute. Retry and cooldown handling comes from the hardened root client. Pacing does not override project-wide daily/token limits. The API credential is read only from an environment variable and is not part of the artifacts.

Run development first to check compatibility and label ambiguity. Freeze the final candidate after any justified development revisions and before viewing test outputs. Record all revisions and whether outputs were already observed. The delivered freeze is a candidate version awaiting independent review, not a claim that this review happened. Do not change test labels or prompts to force improvement after seeing test results.

## Primary outcome and unit

A case decision is correct only if the common output schema is met and both selected option and status equal the answer key. Citation semantics are not included in that primary decision score. The primary pair outcome is 1 only if BOTH variants are correct for a given document order; otherwise it is 0. Average over the two orders, then give each of the 12 pairs equal weight. This penalizes a strategy that gives the same answer to both variants.

Estimate the mean paired difference between evidence checks and generic control. Report an exploratory 95% percentile bootstrap interval, resampling the 12 pair-level differences 10,000 times with seed 711. Compute the baseline contrast as secondary. There is no confirmatory p-value claim. Pairs share mechanisms and construction patterns; resampling pairs does not remove this dependence. Order variants and model responses are not independent sample units. If all conditions reach a ceiling, report it; a zero-width empirical interval does not prove equivalence.

Secondary diagnostics: ordinary case accuracy, schema validity, exact-quote validity, source-set coverage and a mechanical grounded-decision proxy, plus provider failures, token usage, and latency. Source-set coverage uses pre-specified comparison evidence, not an exhaustive list of all semantically valid explanations. Quotations from the right documents can still be irrelevant; only human semantic review can establish explanation support. Report uncertainty and limitations separately from fluent examples.

## Missingness and stopping

The runner persists every completed response, including malformed responses and exhausted transport failures. These count as failed decisions and are reported separately. Resume skips completed jobs and does not retry poor answers. Analysis refuses incomplete schedules, changed frozen files, duplicated jobs or mismatched request hashes. Three successive exhausted errors pause execution; long server cooldowns pause the run and remain binding on resume. No automatic model switching occurs. Preserve technically failed runs and document any replacement.

## Review and ethics

Use REVIEW_RUBRIC.md and the review checklist before evaluation. Ideally a human independently solves the public packets before viewing the answer key, then reconciles disagreement. Record actual reviewers, not fictional names. AI-authored checks can detect construction errors but cannot be reported as human agreement.

There are no real legal, medical or institutional-policy claims. Authority rules are stipulated in fictional settings; this is not verification of authentic provenance. The study excludes retrieval, malicious document instructions, forged signatures, long contexts and downstream user choices. Its results must not be presented as a guarantee that a system can identify truth or make consequential decisions safely.
