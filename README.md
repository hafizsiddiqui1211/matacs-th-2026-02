# MATACS-TH-2026-02: AI Proposal Triage Design

- **Name:** Hafiz Wildan Ahmed Siddiqui
- **Reference:** MATACS-TH-2026-02
- **Role:** Associate Software Developer
- **Time actually spent:** <!-- TODO: write your real time, e.g. "about 3 hours" --> TODO
- **Prototype:** included (optional), see `prototype/README.md`

## Files

| File | What it is |
|---|---|
| [`WRITEUP.md`](WRITEUP.md) | Answers to the five questions, plus my assumptions (including why C and D are flagged and B is ineligible) |
| [`diagram/process-flow.png`](diagram/process-flow.png) | Process flow from upload to ranked output with AI steps, rule-based steps and human checkpoints |
| [`PROMPTS.md`](PROMPTS.md) | The extraction prompt and the reason-writing prompt, exactly as sent |
| [`ranking.json`](ranking.json) | Expected result for proposals A to E |
| [`prototype/`](prototype/) | `score.py` (deterministic scoring, produces `ranking.json`), `criteria.json`, `extracted_facts.json`, optional `extract.py`, `.env.example` |

Run `python prototype/score.py` from the repo root to reproduce the scores (Python 3, no packages needed).

## How I used AI tools

I used Claude to help read the brief, draft the design, the prompts and the prototype code, and to generate the diagram. I reviewed each file and kept the design decisions that I agreed with.

**Where I disagreed with or corrected the AI:** <!-- TODO: replace with ONE real example from your own review, and why. Nobody else can write this for you. --> TODO

## Notes

- Proposals are referred to by letter only. No brief text or proposal text is stored in this repo.
- `extract.py` has not been run against a live API, so it is untested.
