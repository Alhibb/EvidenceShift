# Human review rubric

Review the supplied packet and the response without using outside knowledge. Organisational names and policies are fictional. Do not infer that a more recent upload has more authority or is already effective.

## Dataset review

For each case, confirm: (1) a unique defensible option or explicit unresolved/missing status; (2) consistent query date and effective dates; (3) accurate scope and entity; (4) a gold rationale supported by the packet; (5) all acceptable minimal source sets, including alternatives. Record your identity, date, decision and notes in data/review_checklist.csv. This checklist is initially pending. Structural code checks do not replace this review.

## Output review fields

**justification_supported = 1** only if the explanation accurately reflects the decisive evidence and the quoted passages support the stated explanation. For conflict, it must recognise both incompatible authoritative claims without inventing a priority. For insufficiency, it must not import the other entity's value. Mere citation presence is insufficient. Score 0 for missing, malformed, or unsupported explanations.

**no_unsupported_claims = 1** only if all factual assertions in the explanation are supported by the packet or valid direct inferences. A concise unsupported assumption is still a failure. Score 0 for any invented authority, effective date, scope, or value, and for missing/uninterpretable responses. Do not score tone, fluency or agreement with your own preferences.

Use only 0 or 1. Leave notes for every 0 and every uncertainty. Do not leave blanks in a completed file; resolve ambiguities with an adjudicator where possible. Review the full scheduled set, including failures; never select only impressive examples.

Automated exact-quote and source-set scores are separate. A response can quote a document correctly but draw an unsupported conclusion. Conversely, a valid paraphrase in the explanation may be supported even though the response fails the exact-quote format requirements. Report both aspects.

For two reviewers, preserve separate CSVs, compare agreement before adjudication, record the resolution, and state how disagreements were settled. The supplied summary command summarizes one complete review CSV; it does not calculate inter-rater reliability or certify independence.
