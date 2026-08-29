# EBR Review-by-Exception Engine

A standalone, **configuration-driven** Review-by-Exception (RBE) engine
for electronic batch records. Rules live in JSON files, not in code — the
whole point of this repo is that a reviewer or configuration owner can
retune what gets flagged (tighten a tolerance, block an extra equipment
status, cap a step duration) by editing a JSON file, with zero code
changes and zero redeploy.

This is a companion project to
[`mes-core-model-simulator`](../mes-core-model-simulator), which embeds
its Review-by-Exception rules directly in Python. This repo takes the
opposite, complementary approach — rules as data — to demonstrate both
patterns and the trade-off between them (code rules are easier to unit
test in isolation; config rules are easier for a non-developer reviewer
to safely retune).

## How it works

1. A **rule set** is a JSON file listing rules: an id, a `type` (which
   selects a Python evaluator function from a small registry), a
   description, and `params`.
2. A **batch record** is a JSON file: a batch id and a list of steps,
   each with target/actual values, equipment status, timestamps, an
   optional operator comment, and optional tag readings.
3. `rbe_engine.engine.evaluate_batch()` runs every enabled rule against
   every step, produces an exception report (which steps need a human
   reviewer, and why), and a full audit log (one entry per
   step-per-rule, PASSED or TRIGGERED, timestamped).

## Included rule types (`rbe_engine/rules.py`)

| Type | What it checks |
|---|---|
| `tolerance_check` | actual value vs. target +/- tolerance % |
| `equipment_status_check` | equipment status against a blocklist (e.g. DOWN, DISCONFIGURED) |
| `comment_present` | any operator free-text comment on the step |
| `value_range` | a named tag reading (e.g. UV280) against min/max |
| `duration_check` | step duration against a max-minutes limit |
| `segregation_of_duties` | flags if performed_by == reviewed_by |

Add a new rule type by writing one function with signature
`(step: dict, params: dict) -> str | None` and registering it in
`RULE_REGISTRY` — the engine, loader, and CLI need no changes.

## Quick start

```bash
git clone https://github.com/<your-username>/ebr-review-by-exception-engine.git
cd ebr-review-by-exception-engine
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run both sample batches against the default rule set
python run_demo.py

# Run one batch against the stricter rule set
python run_demo.py --batch sample_batches/batch_with_exceptions.json --rules rules/strict_rules.json

# Write the full audit log to a file
python run_demo.py --audit-out audit_log.json

pytest tests/ -v
```

## Two included rule sets

- `rules/default_rules.json` — 2% dispensing tolerance, blocks
  DOWN/DISCONFIGURED equipment, UV280 must stay under 2.5 AU, steps
  capped at 180 minutes.
- `rules/strict_rules.json` — tighter 2% tolerance override, also blocks
  IN_MAINTENANCE, UV280 capped at 2.0 AU, steps capped at 120 minutes.

`tests/test_engine.py::test_strict_vs_default_rule_sets_differ_on_borderline_value`
shows the same engine code producing different pass/fail outcomes purely
from which rule-set file is loaded — that's the design goal in one test.

## Two included sample batches

- `sample_batches/batch_clean.json` — everything in spec, auto-passes
  100% under both rule sets.
- `sample_batches/batch_with_exceptions.json` — one step out of
  tolerance, one on disconfigured equipment with a comment, one with a
  UV280 excursion and an overlong duration, one with the same user as
  performer and reviewer. Every rule type fires at least once.

## Why this project

Built to demonstrate the "review by exception" pattern named explicitly
in MES Configuration Lead roles — moving batch record review from 100%
manual to rule-driven — in a form where the rule configuration itself
(not just the code) is the deliverable, which is closer to how this
actually gets governed on a real MES platform.

## License

MIT — see `LICENSE`.
