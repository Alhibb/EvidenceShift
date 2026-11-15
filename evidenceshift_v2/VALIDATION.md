# Validation and execution record

Updated 15 November 2026. Runtime: Python 3.12.14, Linux.

## Software

24 tests passed with `python3 -m unittest discover -s tests -q` from inside the project folder. Tests cover dataset invariants, gold-answer fixture scoring, prompt leakage, document-order pairing, strict output parsing, fabricated citations, source coverage, frozen-file drift, credential-safe configuration, provider failure handling, request pacing, Retry-After and RetryInfo, cross-job cooldowns, pause/resume cooldown persistence, and a complete local mock-server pipeline.

The root runner was hardened after completion of the study to propagate server cooldowns across jobs and resumes. The exact implementation used for the study is preserved in frozen_study. Use that archived implementation to analyze the included results. No API failures or retries occurred in either formal run, so this later hardening did not change the experimental outputs.

## Actual Gemini execution

- Model: gemini-3.8-flash, selected after Gemini 2.5 Flash returned an unavailable-model error.
- Configuration: temperature 0, reasoning effort low, max_tokens 4096, JSON object mode.
- Serial pacing: 10 request starts per minute maximum, retries share the limiter.
- Development: 32 responses, 0 transport failures.
- Test: 160 responses, 40 cases, 10 families, 0 transport failures.
- Both test conditions: 100% schema-valid correct decisions and 100% on the mechanical quote/source proxies.
- Reported test tokens: baseline 45,355; evidence checks 50,469.
- Execution paused after 133 test responses due to the execution environment limit and resumed with the same frozen configuration. Completed requests were not repeated.
- Credentials are excluded from project files, output logs and the distributed archive.

## Report and remaining limitations

The five-page PDF was rendered from the DOCX and every page was visually inspected. The main report is four pages, followed by one page of references and required limitations/dual-use material. The abstract has 171 words.

This is a small AI-assisted synthetic pilot with a ceiling effect. Exact quotes and source-set coverage are mechanical checks, not semantic entailment. Dataset and response review checklists remain pending; no independent human reviewers or semantic ratings are invented. The report requires author review before any submission. No repository publication, registration or submission has been performed.

Windows, macOS and Python versions other than 3.12.14 remain untested. The report builder has optional dependencies; the core runner uses only Python's standard library. Rate limiting is local to a single process, so other applications sharing the same project can still consume quotas.
