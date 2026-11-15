# Protocol deviations

No external model evaluation has been performed during package construction.

Record every later deviation here: UTC time, affected version/run, what changed, why, whether any test outputs had already been inspected, and whether the resulting analysis is exploratory. Preserve the original files and results.

14 November 2026: User authorised Gemini access and requested rate limiting. Added serial 10-RPM pacing, Retry-After/RetryInfo handling, jittered bounded backoff and a three-failed-job circuit breaker before formal experiments. Selected gemini-2.5-flash with identical settings for both conditions. Any single connectivity check is development-only and excluded from the planned schedule. Preserved the original package version before edits. Independent human review remains pending.

Preflight update before formal development/test runs: Google returned HTTP 404 for Gemini 2.5 Flash, indicating it is unavailable to new users and recommending gemini-3.8-flash. A minimal compatibility request to gemini-3.8-flash succeeded. Selected this model before any scheduled experiment. Kept the failed preflight record; it is not an evaluated test case.

15 November 2026: The test schedule was interrupted after 133 saved responses by the execution environment's usage limit. Resumed the same frozen configuration; request 134 was recorded on 15 November. No completed job was rerun. A local payload audit confirmed that all outgoing packets were generated fictional notices and that answer keys, private user files and real email addresses were absent. Record timestamps preserve the interruption.

After completion of the 160-call test schedule, hardened cross-job and resumed-run cooldown handling. Archived the exact experimental source in frozen_study before this code change. Experimental outcomes, prompts, labels and scoring were not changed.
