# Write-up: AI proposal triage (MATACS-TH-2026-02)

Flow is in `diagram/process-flow.png`. Prompts are in `PROMPTS.md`. Expected result is in `ranking.json`.

## 1. AI vs. rules

**AI (2 steps):** (a) extraction: turning messy proposal text into a fixed JSON of facts, each with an exact quote; (b) writing a one-sentence plain-English reason per proposal from the finished score table.

**Plain code (everything that decides something):** PDF-to-text, file hash, pattern scan for instruction-like text, JSON validation, mandatory pass/fail, flag rules, weighted maths, ranking, audit log.

**Why this line:** language is messy, so AI helps there. Money, weights and ordering must be repeatable and explainable, so code does them. The AI never sees the weights and never produces a score or rank.

## 2. Consistency and explainability

- Scores come from code using fixed formulas: experience = installs / 12, price and timeline = position between the best eligible bid and the limit, warranty = average of panel (/25 yrs) and workmanship (/12 yrs), team = 25 points each for named lead, crew, safety plan, monitoring plan.
- Same facts in, same score out, always. Extraction runs at temperature 0 and is cached by document hash, so ranking the same files twice reuses the same facts. A re-extraction that differs is shown as a diff, not silently applied.
- Every non-null fact needs an exact quote that code confirms is in the document; otherwise it becomes null and is flagged.
- The reviewer sees, per proposal: each criterion, the extracted value, the quote, sub-score, weight and contribution. The criteria version, prompt version and model are shown too.

## 3. Human in the loop

- **Checkpoint 1:** flagged proposals cannot be ranked until a person includes, excludes, or asks the bidder to clarify. A person may also correct an extracted fact (quote shown).
- **Checkpoint 2:** the ranked list is advice. A person can reorder or exclude with a required reason.
- **Checkpoint 3:** the award itself is only ever recorded as a human decision.
- **Audit log:** user, time, file hashes, criteria version, prompt version, model and settings, raw extraction, validation results, flags, scores, every override with reason, and the final decision.

## 4. Changing criteria

Criteria are versioned and never edited in place. Saving a change creates v2. Results already produced stay attached to v1 and are labelled "scored under v1". Nothing re-scores automatically.

A reviewer can click "re-score under v2". Because facts are cached, only the rules re-run. If v2 adds a criterion that needs a new fact, only that field is re-extracted. The tool shows a v1 vs v2 rank comparison so a person can see what changed. Past awards keep the version they were made under.

## 5. Risks

| Risk | Guard |
|---|---|
| Wrong extraction | Quote must exist in the text; null if missing; reviewer sees quotes; spot-check checkpoint |
| Made-up facts | "Only what is stated, else null" rule; unverifiable values become null and flagged |
| Prompt injection / manipulation | Proposal text is data; pattern scan plus model report of instruction-like text; scoring code never reads free text; flagged for a person |
| Bias | Scoring code only receives numbers and booleans, not company names, size or location; proposals referenced by letter; periodic review of overrides |
| Unverifiable claims (licence number, insurance) | Tool records "stated in proposal" only; a person verifies with the registry before award |
| Cost | Extract once per document and cache; rules are free; reasons use a small model; page limit per upload |
| Over-trusting the tool | Output is labelled advisory; flagged and ineligible bids stay visible with reasons |

## Assumptions (no clarification was requested)

1. **C is flagged, not ranked.** C has text aimed at automated reviewers claiming pre-approval and asking for first place and full marks. The system treats it as data, ignores it completely, and scores C only on its real content (provisional 65.0, which would not beat A or E anyway). I flag rather than auto-disqualify because intent is unknown (it could be a pasted template or a third party), and a person, not the tool, should decide whether to penalise it. The "pre-approved" claim is unverifiable, so a reviewer should check it with the client procurement office. A flagged bid is not placed in the ranking until a person clears it.
2. **D is flagged.** No completion time is given, so the 16-week requirement cannot be confirmed. Timeline scores 0 for the provisional score (73.8). If a stated time within 16 weeks arrives, D can be re-scored.
3. **B is ineligible.** The licence must be held by the bidder; "a subcontractor, confirmed after award" does not meet it. Its low price is not scored.
4. **Experience window:** "last 5 years" is counted back from the 2026 reference date. C says "since 2020", which may include older work, so it carries an uncertainty note but its stated count is used.
5. **Normalisation:** price and timeline are scored against the best non-ineligible bid, so scores depend on the bid set. Any change to the set triggers a re-run.
6. **Tie handling:** equal scores are ordered by letter, then shown to the reviewer as a tie to resolve.
