"""
engine.py — loads a JSON rule set and a JSON batch record, evaluates
every step against every enabled rule, and produces an exception report
plus an in-memory audit trail (a list of dicts; write it wherever you
like — file, DB, stdout).
"""

import json
from datetime import datetime, timezone
from .rules import RULE_REGISTRY


class UnknownRuleType(ValueError):
    pass


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_rule_set(path):
    with open(path) as f:
        rule_set = json.load(f)
    for rule in rule_set["rules"]:
        if rule.get("enabled", True) and rule["type"] not in RULE_REGISTRY:
            raise UnknownRuleType(
                f"Rule {rule['id']} uses unknown type '{rule['type']}'. "
                f"Known types: {sorted(RULE_REGISTRY)}"
            )
    return rule_set


def load_batch(path):
    with open(path) as f:
        return json.load(f)


def evaluate_batch(batch: dict, rule_set: dict):
    """Returns (report, audit_log).

    report = {
      "batch_id": ...,
      "rule_set_name": ...,
      "total_steps": N,
      "auto_passed": N,
      "exceptions": [{"step_id":..., "triggered_rules": [{"rule_id":..., "reason":...}]}]
    }
    """
    audit_log = []
    exceptions = []
    auto_passed = 0

    active_rules = [r for r in rule_set["rules"] if r.get("enabled", True)]

    for step in batch["steps"]:
        triggered = []
        for rule in active_rules:
            fn = RULE_REGISTRY[rule["type"]]
            reason = fn(step, rule.get("params", {}))
            audit_entry = {
                "timestamp": now_iso(),
                "batch_id": batch["batch_id"],
                "step_id": step["step_id"],
                "rule_id": rule["id"],
                "rule_type": rule["type"],
                "result": "TRIGGERED" if reason else "PASSED",
                "reason": reason,
            }
            audit_log.append(audit_entry)
            if reason:
                triggered.append({"rule_id": rule["id"], "description": rule.get("description", ""),
                                   "reason": reason})

        if triggered:
            exceptions.append({"step_id": step["step_id"], "triggered_rules": triggered})
        else:
            auto_passed += 1

    report = {
        "batch_id": batch["batch_id"],
        "rule_set_name": rule_set.get("rule_set_name", "unnamed"),
        "rule_set_version": rule_set.get("version"),
        "total_steps": len(batch["steps"]),
        "auto_passed": auto_passed,
        "exception_count": len(exceptions),
        "review_load_reduction_pct": round(auto_passed / len(batch["steps"]) * 100, 1) if batch["steps"] else 0,
        "exceptions": exceptions,
    }
    return report, audit_log


def evaluate_batch_file(batch_path, rule_set_path):
    batch = load_batch(batch_path)
    rule_set = load_rule_set(rule_set_path)
    return evaluate_batch(batch, rule_set)
