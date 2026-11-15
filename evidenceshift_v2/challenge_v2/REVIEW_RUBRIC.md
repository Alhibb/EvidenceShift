# Dataset and output review rubric

## Solve before checking labels

Read a public packet without its answer key. Select one of the four options, choose answer/conflict/insufficient status, list the decisive sources and briefly explain why the competing substantive answer does not follow. Use only the fictional rules in the packet; do not import real-world legal or organizational assumptions.

Then compare against data/answer_key.jsonl or the labelled review checklist. Record accepted, revise or reject, your actual name, and the reason. The initial checklist is pending. If the key is ambiguous or wrong, revise before test evaluation, preserve the previous version and generate a new freeze. Do not interpret automated structural checks as human annotation.

## Case acceptance requirements

1. The question specifies a sufficiently clear target, time or event.
2. The controlling rule and required facts are available, or the missing/conflicting information is intentional.
3. Exactly one option follows under the packet's rules. Plausibility from outside knowledge is insufficient.
4. The rationale identifies the necessary authority, scope, time or version relationship.
5. The comparison-evidence source set is defensible. Mark alternative valid explanations for later human scoring.
6. The paired case changes only one document text and that change alone changes the defensible answer.
7. No private information, accidental instructions to the model, or answer labels appear in the public packet.

## Mechanism-specific questions

| Mechanism | What the reviewer must establish |
|---|---|
| Effective time | Is the relevant event before or after the operative date or cohort cutoff? |
| Partial scope | Does the amendment cover the exact object or weight band? |
| Authority | Did the issuer hold the necessary power, within its stated bounds and appointment dates? |
| Version history | Which effective, unwithdrawn issued notice controls, independently of upload time? |
| Unresolved conflict | Is there a valid precedence or reconciliation rule, or must disagreement remain unresolved? |
| Missing information | Is the needed target fact actually present, rather than merely an adjacent or proposed fact? |

## Response review after the run

Separate decision correctness from semantic evidence support. Score justification_supported as 1 only if the explanation and cited passages support the decisive inference without inventing priority, scope, dates or authority. Score no_unsupported_claims as 1 only if all factual statements follow from the packet. Use 0 for missing, malformed or unsupported explanations. Retain notes and disagreements. Exact quote matching is lexical and cannot substitute for this assessment.

Hide condition labels from response reviewers; wording may still reveal the treatment, so blinding is imperfect. If only one reviewer participates, report that. Do not claim inter-rater agreement without at least two actual independent annotations. No human semantic scores are supplied in this candidate release.
