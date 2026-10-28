# Prototype (optional)

- `score.py` : deterministic rules + weighted scoring + ranking (stdlib only, no AI). Run `python prototype/score.py --out ranking.json` from the repo root. This is how `ranking.json` was produced (the one-line reasons were then edited by hand).
- `criteria.json` : example admin-defined criteria (nothing hard-coded in `score.py`).
- `extracted_facts.json` : the validated facts per proposal letter that the extraction step would return. No proposal text is stored here.
- `extract.py` : optional extraction step that runs the prompt in `PROMPTS.md`. It reads proposal text from a local, git-ignored `samples/` folder and needs an API key (`.env.example`). I could not run it against a live API while building this repo, so treat it as untested.
