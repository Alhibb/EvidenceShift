# EvidenceShift

A small, reproducible experiment on how an assistant handles conflicting dates, authority and incomplete evidence.

**Status: 32 development responses and 160 test responses completed using Gemini 3.8 Flash. Both test conditions achieved 100% decision accuracy. Independent human review and author approval remain pending.**

The package contains 40 fictional test cases, eight development cases, two prompts, a standard-library Python HTTP runner, strict output scoring, paired family-bootstrap analysis, blinded review exports and a report scaffold. It is a controlled evaluation of the answering stage with supplied documents, not a complete retrieval system.

## Start here

Requires Python 3.10 or newer. Tested locally with Python 3.12.14; other versions have not been tested. No pip packages are required. Extract this folder and run commands from inside it. On Windows, use `py` instead of `python3` if appropriate.

```bash
python3 evidenceshift.py validate
python3 -m unittest discover -s tests -v
```

Read `docs/PROTOCOL.md`, then inspect `data/review_checklist.csv` and `data/test.jsonl`. The generated labels have structural checks and explicit rationales, but no independent human approval. Review before treating results as publishable.

## Configure a model

Copy `config.example.json` to `config.local.json`. Replace the model placeholder with a model available on your account and choose its supported request parameters. The default endpoint uses Chat Completions. Any compatible provider may be used, but compatibility must be verified on the development set. For a local server, use its `http://localhost:PORT/v1` URL and model ID. The runner refuses remote plaintext HTTP and credential-bearing URLs.

Set `EVIDENCESHIFT_API_KEY` in your environment. Never put credentials in JSON files, source, chat, or the report. PowerShell can prompt without putting the key in command history:

```powershell
$env:EVIDENCESHIFT_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'API key' -AsSecureString)).Password
```

Bash equivalent:

```bash
read -rsp 'API key: ' EVIDENCESHIFT_API_KEY
export EVIDENCESHIFT_API_KEY
```

There is no key configured in the delivered project. Model access and API charges are separate from this package. A full test run schedules 160 calls at one repeat, and a development run schedules 32; transient retries can increase actual billed attempts. The runner reports usage returned by the provider, not a guaranteed monetary cost. Set a provider-side spending limit and inspect the development run before the full test.

## Development, freeze, then test

The included `freeze.json` describes the delivered version. A freeze checks code, data, protocol and prompts before execution and analysis. Review notes can be recorded separately; any changes to frozen files require a new freeze and a new run directory. A hash file is not public preregistration.

```bash
python3 evidenceshift.py run --config config.local.json --freeze freeze.json --split dev --out runs/dev --plan
python3 evidenceshift.py run --config config.local.json --freeze freeze.json --split dev --out runs/dev
python3 evidenceshift.py analyze runs/dev
```

After development and dataset review, if the frozen files changed:

```bash
python3 evidenceshift.py freeze --out freeze.final.json
```

Use the selected freeze consistently below (`freeze.json` if nothing changed):

```bash
python3 evidenceshift.py run --config config.local.json --freeze freeze.json --split test --out runs/test --plan
python3 evidenceshift.py run --config config.local.json --freeze freeze.json --split test --out runs/test
python3 evidenceshift.py analyze runs/test
python3 evidenceshift.py export-review runs/test --out runs/review
```

Repeating the identical run command resumes unfinished jobs. Completed wrong answers, malformed responses and transport failures are not silently rerun. Do not run two processes against one run directory. Config changes require a new directory. Analysis refuses incomplete or mismatched runs. A truncated final log line causes an explicit error; preserve a copy before manually repairing only the interrupted line.

Have a reviewer complete `runs/review/review_blinded.csv` using `docs/REVIEW_RUBRIC.md`. Share only that CSV, not `review_private_key.json`. The response style may still reveal the prompt condition. To summarize a completed file:

```bash
python3 evidenceshift.py review-summary runs/test --csv runs/review/review_blinded.csv --key runs/review/review_private_key.json
```

Generated artifacts: `manifest.json`, `responses.jsonl`, `scores.csv`, `summary.json`, `summary.md`, and optional `human_review_summary.json`. Keep every original run, even failed or unfavourable runs. No network call occurs during validation, freeze, plan, analysis, or tests outside a local mock server used by tests.

## Interpretation

The primary score requires a correctly selected option and status in a valid response. It is constrained-choice accuracy, not free-form factual accuracy. The paired analysis clusters related cases by ten domain families. Both document orders and repeated calls are dependent observations. The bootstrap interval is exploratory.

Exact quotes and gold source coverage are mechanical proxies. They cannot certify semantic support or count hallucinated claims in free text. Human review handles those judgments. The two-arm treatment changes several instructions and prompt length together; no component-level causal claim is justified.

Related work already studies conflicting evidence and prompting. This project should be presented as a limited replication/extension, with modest scope and explicit limitations. See `docs/RELATED_WORK.md`.

## Sprint handoff

Use `docs/REPORT_SCAFFOLD.md` after running and reviewing the experiment. It deliberately contains no invented findings. The official event requires its own report template and a maximum eight-page main report, excluding references and appendices. The report scaffold is not that template and is not submission-ready. See `docs/SPRINT_CHECKLIST.md` for the source and checklist.

## Files

| Path | Purpose |
|---|---|
| `evidenceshift.py` | Runner, validation, freeze, scoring, analysis and review commands |
| `make_dataset.py` | Deterministic fictional data generator; do not regenerate after freezing |
| `data/` | Test/development packets, gold labels and human review checklist |
| `prompts/` | Both interventions and identical output requirements |
| `tests/` | Scoring, leakage, reproducibility, provider failure and end-to-end checks |
| `docs/` | Protocol, sources, reviewer rubric, report scaffold and execution handoff |
| `VALIDATION.md` | Actual local validation record and remaining limitations |

No public repository, deployment, sprint registration or submission has been performed by creating this package. Choose a code/data licence before publishing; none is imposed here.

## Gemini configuration and rate limiting

Use `config.gemini.json` and `freeze.gemini.json` for NEW experiments with the hardened root runner. Use `frozen_study/evidenceshift.py` to reproduce the included study analysis. The credential is read from `EVIDENCESHIFT_API_KEY`; no key is included. The chosen model is gemini-3.8-flash. Example:

```bash
python3 evidenceshift.py run --config config.gemini.json --freeze freeze.gemini.json --split dev --out runs/gemini-dev-new
```

Pacing is 10 request starts/minute, one serial request at a time, with retries consuming the same allowance. Server Retry-After and Google RetryInfo delays override shorter exponential backoff. Maximum three attempts per job, with jitter; a cooldown longer than 120 seconds pauses the entire run and its remaining duration is respected on resume. Cooldowns also carry forward to subsequent jobs. Three consecutive failed jobs pause the run. Authentication or configuration errors stop immediately. Resume retains failures and does not re-run them. Quotas are project-wide; other apps and token/day limits can still cause 429 errors. Do not run multiple processes using the same key and assume this local limiter coordinates them. Review active account limits at https://aistudio.google.com/rate-limit .


## Completed study and report

Start with `report/EvidenceShift_Research_Report.pdf` (five pages: four main pages plus references/appendices) or the editable DOCX. The report is a review draft and no submission has been made.

The test completed 160 responses over 40 cases with zero transport failures. Both prompts achieved 100% decision accuracy. Baseline used 45,355 reported tokens; evidence checks used 50,469 (11.3% more). This indicates a ceiling in this small synthetic pilot, not proof of equivalence on realistic tasks. The development run completed 32 responses separately. Human semantic scores remain unmeasured.

Reproduce the existing results without any API key or network call:

```bash
python3 frozen_study/evidenceshift.py analyze runs/gemini-dev
python3 frozen_study/evidenceshift.py analyze runs/gemini-test
```

The exact experimental code is archived in `frozen_study`. After the study, the root runner gained cross-job and resumed-run cooldown enforcement, verified by the expanded 24-test suite. The archived source and manifests preserve the version actually used; no test response required a retry. Root-runner analysis deliberately refuses an old source hash, so use the commands above for the included runs.

For semantic review, share only `runs/review/review_blinded.csv` with the reviewer. Keep the mapping file separate. After complete ratings are returned:

```bash
python3 frozen_study/evidenceshift.py review-summary runs/gemini-test --csv runs/review/review_blinded.csv --key runs/review/review_private_key.json
```

Optional report regeneration requires python-docx and matplotlib, beyond the standard-library experiment runner. Run `python3 report/build_report.py runs/gemini-test`, then render the DOCX to PDF and inspect every page. The distributed PDF was visually checked on all five pages.
