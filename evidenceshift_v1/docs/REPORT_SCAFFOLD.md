# EvidenceShift: A Controlled Pilot of Temporal and Authority Checks in Document-Grounded Decisions

**WORKING SCAFFOLD — NO EMPIRICAL MODEL FINDINGS YET — NOT READY FOR SUBMISSION**

Proposed author: Ibrahim Rabiu, DevClans Solution LTD. Confirm the affiliation and add only actual contributors.

## Abstract

Write 150–250 words after the experiment: problem; controlled design; model and number of independent families; actual primary result and interval; principal failure category; limitations. Do not replace missing results with expectations. This scaffold intentionally contains no purported findings.

## 1. Introduction

Document-grounded assistants may encounter newer material that is not yet effective, not approved, unofficial, or a repost of older material. A date-only heuristic can be inadequate. We ask whether an explicit evidence-checking prompt changes constrained decisions on a small, controlled synthetic evaluation. This is a replication-oriented pilot, not a claim to introduce conflicting-evidence evaluation.

## 2. Related work

Discuss Wang et al. (2025), RAMDocs/MADAM-RAG, and Cattan et al. (2025), CONFLICTS. Read the full papers before finalising this section. Explain the exact overlap and remaining scope; do not describe the broad intervention as novel. See RELATED_WORK.md for verified links and abstract-level notes.

## 3. Method

Describe the 40 test cases across 10 families, eight development cases, four categories, five resolved-discrepancy mechanisms, and two document orders. State the fictional construction process, AI assistance, any human review, annotation disagreements and changes. Explain the common response schema, randomised option positions, paired inputs, model revision, provider, generation parameters and run dates. Distinguish supplied-document generation from end-to-end retrieval. Include frozen prompt and dataset hashes in an appendix or repository.

The primary outcome requires schema-compliant correct option and status. Estimate the paired family mean difference; report the exploratory 10,000-draw family-bootstrap interval. Disclose all transport/format failures and incomplete or abandoned runs. The longer treatment is a combined intervention without a length-matched control.

## 4. Results — populate only from completed run artifacts

| Measure | Baseline | Evidence checks |
|---|---:|---:|
| Decision accuracy | NOT RUN | NOT RUN |
| Schema compliance | NOT RUN | NOT RUN |
| Exact quote validity | NOT RUN | NOT RUN |
| Grounded-decision proxy | NOT RUN | NOT RUN |
| Human-supported justification | NOT REVIEWED | NOT REVIEWED |

Add primary difference and uncertainty, category results, order sensitivity, transport errors, token usage and latency. State actual reviewer counts. Use representative failures selected by a declared rule, such as all changed decisions or the first error by sorted case ID; avoid cherry-picking examples. Report a null or negative result as such.

## 5. Discussion

Interpret only the actual evidence. A ceiling effect would limit the ability to distinguish prompts; a positive effect would establish at most a within-model effect on these legible synthetic packets. Do not extrapolate to human decision quality, authentic source verification, all models, or full RAG pipelines. Describe a next experiment on independently annotated realistic conflicts.

## References

Wang, H., Prasad, A., Stengel-Eskin, E., & Bansal, M. (2025). Retrieval-Augmented Generation with Conflicting Evidence. https://arxiv.org/abs/2504.13079

Cattan, A., et al. (2025). DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs. https://arxiv.org/abs/2506.08500

## Appendix A. Limitations and Dual-Use / Ethical Considerations

All cases are fictional and contain no personal data. Ten test families share templates; two order variants and repeated calls are not independent observations. Explicit authority labels may simplify the task and produce ceiling effects. The options constrain generation and may cue abstention. Date and authority stipulations are trusted; they are not verified against real sources. The treatment is longer, so its components are confounded. Exact quotation and source coverage do not establish semantic entailment. Human review is required for semantic claims; disclose reviewer independence and imperfect blinding. The study does not test prompt injection, forged evidence, long contexts, retrieval errors, or downstream user decisions. Findings could help attackers craft misleading authoritative-looking documents. Preserve human verification and do not present the system as a truth oracle.

## Appendix B. Contribution and AI-use statement

Record the actual implementation dates and contributor responsibilities. This package was constructed with AI assistance on 14 November 2026. Synthetic data, code and drafting were AI-assisted; no independent human review or external model evaluation took place during construction. Update this statement with actual later work and identify any code predating the sprint. Do not invent affiliations, collaborators or experiments.
