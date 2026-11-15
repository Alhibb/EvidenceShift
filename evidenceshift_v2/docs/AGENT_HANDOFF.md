# Current state

The Gemini pilot is now complete. Read the report and existing run artifacts before making new API calls. Use frozen_study/evidenceshift.py for existing-run analysis; the root runner includes later cooldown hardening for new runs. Independent human review remains pending. Preserve the ceiling-effect result rather than modifying the completed test to obtain an improvement.

# Execution handoff for a coding assistant

You are continuing EvidenceShift, a small research pilot. Read README.md, PROTOCOL.md, RELATED_WORK.md and VALIDATION.md before changing anything. Do not claim an empirical result from tests, fixtures, demonstrations or your own answers to the test cases.

1. Check Python and run validation/tests. Preserve the delivered version and freeze.
2. Obtain a user-configured provider endpoint/model and an API key through an environment variable or secret manager. Never ask for the key in chat, read unrelated credentials, or invent model access. Local compatible model servers are supported.
3. Review all gold labels with a real human when available. Record actual review status. Do not claim that AI self-checks are independent human review.
4. Run only the development split first. Investigate API compatibility, truncation and any ambiguity. Log changes and new freezes. Do not inspect test outputs and then tune prompts on them.
5. Before final evaluation, fix model ID, parameters, number of repeats, dataset, primary outcome and analysis. Use one model as the main pilot; any added models must be labelled exploratory unless planned before results.
6. Execute the full planned test schedule with the frozen runner; preserve raw outputs. Do not retry poor answers, silently remove failed cases, alter gold labels to match outputs or cherry-pick runs.
7. Analyze and export blinded review. Keep the mapping secret from reviewers. Aggregate complete human annotations and preserve disagreements if two reviewers participate.
8. Write findings only from artifacts. Distinguish exact quote matching from semantic support, constrained choices from free-form QA, and supplied-context generation from end-to-end RAG. Acknowledge prior conflicting-evidence work and possible ceiling effects.
9. Move the report into the organiser's official template, include limitations/dual-use appendix, render to PDF and visually inspect every page. Verify the abstract length and eight-page main-text limit.
10. Prepare a repository only if requested; exclude keys, private review mapping and unnecessary provider metadata. Do not register, publish or submit merely because this handoff mentions those steps.

The task is not complete scientifically until real model outputs and honest review support the report. If access is missing, return an exact blocker with a runnable command; never replace an experiment with invented numbers.
