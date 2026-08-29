import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from rbe_engine.engine import evaluate_batch, load_rule_set, load_batch, UnknownRuleType

ROOT = Path(__file__).resolve().parent.parent


def test_clean_batch_fully_auto_passes():
    batch = load_batch(ROOT / "sample_batches" / "batch_clean.json")
    rule_set = load_rule_set(ROOT / "rules" / "default_rules.json")
    report, audit_log = evaluate_batch(batch, rule_set)
    assert report["exception_count"] == 0
    assert report["auto_passed"] == report["total_steps"]
    assert report["review_load_reduction_pct"] == 100.0


def test_exception_batch_flags_every_step():
    batch = load_batch(ROOT / "sample_batches" / "batch_with_exceptions.json")
    rule_set = load_rule_set(ROOT / "rules" / "default_rules.json")
    report, audit_log = evaluate_batch(batch, rule_set)
    assert report["exception_count"] == report["total_steps"]
    assert report["auto_passed"] == 0

    flagged_steps = {e["step_id"] for e in report["exceptions"]}
    assert flagged_steps == {"S1", "S2", "S3", "S4"}


def test_audit_log_has_one_entry_per_step_per_rule():
    batch = load_batch(ROOT / "sample_batches" / "batch_clean.json")
    rule_set = load_rule_set(ROOT / "rules" / "default_rules.json")
    report, audit_log = evaluate_batch(batch, rule_set)
    expected = len(batch["steps"]) * len(rule_set["rules"])
    assert len(audit_log) == expected
    assert all(e["result"] in ("PASSED", "TRIGGERED") for e in audit_log)


def test_disabled_rule_is_skipped():
    batch = {"batch_id": "B1", "steps": [{"step_id": "S1", "target_value": 10, "actual_value": 999}]}
    rule_set = {
        "rule_set_name": "test", "version": 1,
        "rules": [{"id": "R1", "type": "tolerance_check", "enabled": False, "params": {}}],
    }
    report, audit_log = evaluate_batch(batch, rule_set)
    assert report["exception_count"] == 0
    assert audit_log == []


def test_unknown_rule_type_raises(tmp_path):
    bad_rules = tmp_path / "bad.json"
    bad_rules.write_text(
        '{"rule_set_name": "bad", "version": 1, '
        '"rules": [{"id": "R1", "type": "not_a_real_rule", "params": {}}]}'
    )
    with pytest.raises(UnknownRuleType):
        load_rule_set(bad_rules)


def test_strict_vs_default_rule_sets_differ_on_borderline_value():
    """A step that passes the looser default 5% tolerance but fails a
    3% strict override — proves the same engine code produces different
    outcomes purely from rule-set config, which is the whole point."""
    batch = {"batch_id": "B1", "steps": [
        {"step_id": "S1", "target_value": 100.0, "actual_value": 104.0, "tolerance_pct": 5.0}
    ]}
    loose = {"rule_set_name": "loose", "version": 1,
             "rules": [{"id": "R1", "type": "tolerance_check", "params": {}}]}
    strict = {"rule_set_name": "strict", "version": 1,
              "rules": [{"id": "R1", "type": "tolerance_check", "params": {"tolerance_pct": 3.0}}]}

    loose_report, _ = evaluate_batch(batch, loose)
    strict_report, _ = evaluate_batch(batch, strict)

    assert loose_report["exception_count"] == 0
    assert strict_report["exception_count"] == 1
