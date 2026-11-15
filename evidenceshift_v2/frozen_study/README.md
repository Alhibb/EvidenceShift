# Frozen experiment implementation

These are the exact code, prompts, data and protocol used for the delivered Gemini development and test runs. Use this version to verify and reproduce their analysis from the project root:

```bash
python3 frozen_study/evidenceshift.py analyze runs/gemini-dev
python3 frozen_study/evidenceshift.py analyze runs/gemini-test
```

Use the root runner for NEW experiments. After the completed study, its rate limiter was hardened so a server cooldown also persists across subsequent jobs and resumes. This archived version is retained for research provenance, not recommended for new API execution. No quota response occurred in the delivered study if the run summaries and raw logs report none; consult those artifacts rather than assuming.
