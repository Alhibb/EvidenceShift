# EvidenceShift challenge study

This is a separately versioned follow-up to the completed ceiling-effect pilot. It contains a new dataset, scoring rubric, three prompts and an executable experiment harness. **Completed: 36 development and 144 test responses from Gemini 3.8 Flash, with zero transport failures.** Independent human label review is pending. See `report/EvidenceShift_Challenge_Report.pdf` for the report and `runs/test/summary.json` for exact scores.

## What changed

| Design choice | Completed pilot | Challenge study |
|---|---|---|
| Test cases | 40 single cases | 24 cases in 12 counterfactual pairs |
| Documents per packet | 2 | 4 |
| Conditions | Baseline and evidence checks | Baseline, generic control and evidence checks |
| Generic versus targeted instruction | Not controlled | Both 77 whitespace-delimited words |
| Primary unit | Domain family | Counterfactual pair |
| Primary outcome | Correct case decision | Both variants correct |

Each pair changes one document text while holding the question, answer choices and source metadata fixed. The correct answer must change. Six mechanisms cover operative dates, partial amendments, delegation, version history, unresolved conflicts and missing target facts. This is designed to require more cross-document reasoning; the observed score reduction is confounded by an implicit packet-applicability convention. Similar word length does not imply equal tokenizer length or inference compute.

The candidate contains 24 test cases and six development cases. The test has 20 answer, two conflict and two insufficient-information cases, so abstention estimates will be weak. Read PROTOCOL.md for the limitations and prespecified comparisons.

## Review before evaluation

Use REVIEW_PACK.md to read the cases, REVIEW_RUBRIC.md to solve them, and data/review_checklist.csv to record actual review decisions. Ideally solve the public JSON packets before consulting the key. Review fields start pending. No independent reviewer or agreement score has been invented. Record any corrections and freeze a new version before inspecting test responses.

## Commands

From this `challenge_v2` directory, Python 3.10+:

```bash
python3 challenge.py validate
python3 -m unittest discover -s tests -v
python3 challenge.py run --split dev --out runs/dev --plan
```

These commands are offline. The included candidate freeze covers code, prompts, public packets, answer keys, protocol, rubric, parent API client and parent Gemini config. Any edits to those files require a new freeze path; preserve the old version.

After dataset review and configuring the API-key environment variable, the planned development run is 36 calls:

```bash
python3 challenge.py run --split dev --out runs/dev
python3 challenge.py analyze runs/dev
```

The planned test run is 144 calls, three conditions × 24 cases × two document orders:

```bash
python3 challenge.py run --split test --out runs/test --plan
python3 challenge.py run --split test --out runs/test
python3 challenge.py analyze runs/test
```

The key is not included. The harness reuses the parent's hardened Gemini client with 10-RPM serial pacing, bounded retries and persisted cooldowns. All packets are generated fictional data, with no private user files. No network call occurs until an explicit `run` without `--plan`. Repeating an identical command resumes unfinished jobs without rebilling completed ones. Use one process per directory; do not assume the limiter coordinates other apps using the same account.

## Scoring and interpretation

The primary comparison is evidence checks versus the generic control; baseline is secondary. A pair earns full success only if both changed scenarios are answered correctly. The two document orders are averaged within each pair. Twelve pair clusters support exploratory uncertainty only. Model outputs, order variants and repeated templates are not independent observations.

The source-set and quote scores remain mechanical proxies. Use a real reviewer for semantic support claims. If every condition still reaches 100%, retain that outcome and report another ceiling; do not alter the completed test to manufacture an improvement.

## Provenance

Case narratives and keys were authored with AI assistance on 15 November 2026 after seeing the earlier pilot results. The reviewed test has been run; its data and prompts were not modified after inspecting outputs. Public inputs and answer keys are stored separately; only question, options and documents enter model requests. All organisations and policies are fictional. Original pilot code, data and empirical outputs remain unchanged.

## Completed results

| Metric | Baseline | Generic control | Evidence checks |
|---|---:|---:|---:|
| Pair accuracy | 79.2% | 83.3% | 75.0% |
| Case decision accuracy | 81.25% | 87.5% | 79.17% |
| Reported tokens | 33,647 | 36,995 | 35,371 |

The primary paired difference is -8.33 percentage points (exploratory bootstrap interval -20.83 to 0). Only 12 pair units are available. Post-hoc AI inspection found all 25 scored failures questioned whether the documents applied to the organisation named in the question: 24 abstentions and one keyed answer that exceeded the explanation-length limit. Two responses in total violated the length limit. This is a construct-validity problem, not clean evidence of failed temporal or authority reasoning. Labels were not changed to improve the score.

Reproduce results offline with `python3 challenge.py analyze runs/test`. `DEVELOPMENT_FINDINGS.md` records the earlier development observation and decision to retain the frozen test. `runs/test/error_audit.csv` records the post-hoc AI inspection. For independent semantic review, share only `runs/review/review_blinded.csv`, keeping its mapping separate; no ratings are claimed as completed.

The test was interrupted after three responses and resumed without repeating them. All 144 jobs passed schedule and request-hash verification. Report sources and implementation are included. No public repository or sprint submission has been created.
