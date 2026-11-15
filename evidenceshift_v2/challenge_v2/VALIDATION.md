# Validation record

15 November 2026. Seven offline tests passed after pre-run wording clarification. Structural checks cover 24 test cases in 12 pairs, six development cases in three pairs, private-label exclusion, document-order reversal, primary scoring, incomplete-run rejection and frozen-source drift rejection. Test fixtures are not empirical model results.

Actual Gemini execution completed 36 development and 144 test responses. All test job IDs and request hashes match the frozen schedule, with no duplicate jobs and zero transport failures. Test was resumed after an interruption at three responses. The original and reviewed freezes are retained.

Pair accuracy: baseline 79.17%, generic control 83.33%, evidence checks 75.00%. Primary difference -8.33 percentage points, exploratory paired bootstrap interval [-20.83, 0.00]. Source matching and quote checks are mechanical proxies only.

AI inspection of all 25 scored failures identified an implicit organisation-to-packet association problem. This confounds claims about reasoning performance. Review was not independent or human; semantic reviewer fields remain blank. See DEVELOPMENT_FINDINGS.md and runs/test/error_audit.csv. Frozen data, prompts and protocol were not changed after outputs were inspected.
