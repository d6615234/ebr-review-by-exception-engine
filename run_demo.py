"""
run_demo.py — run the RBE engine against the sample batches with both
included rule sets, and print a readable summary.

Usage:
    python run_demo.py
    python run_demo.py --batch sample_batches/batch_with_exceptions.json --rules rules/strict_rules.json
"""

import argparse
import json
from pathlib import Path

from rbe_engine.engine import evaluate_batch_file

ROOT = Path(__file__).resolve().parent


def print_report(report):
    print(f"\nBatch {report['batch_id']}  |  rule set: {report['rule_set_name']} v{report['rule_set_version']}")
    print(f"  Steps: {report['total_steps']}  |  Auto-passed: {report['auto_passed']}  |  "
          f"Exceptions: {report['exception_count']}  |  "
          f"Review load reduction: {report['review_load_reduction_pct']}%")
    for exc in report["exceptions"]:
        print(f"    EXCEPTION step {exc['step_id']}:")
        for rule in exc["triggered_rules"]:
            print(f"      - [{rule['rule_id']}] {rule['reason']}")


def main():
    parser = argparse.ArgumentParser(description="Run the Review-by-Exception engine")
    parser.add_argument("--batch", default=None, help="Path to a single batch JSON file")
    parser.add_argument("--rules", default=str(ROOT / "rules" / "default_rules.json"))
    parser.add_argument("--audit-out", default=None, help="Optional path to write the full audit log as JSON")
    args = parser.parse_args()

    if args.batch:
        batch_paths = [Path(args.batch)]
    else:
        batch_paths = sorted((ROOT / "sample_batches").glob("*.json"))

    all_audit = []
    for batch_path in batch_paths:
        report, audit_log = evaluate_batch_file(batch_path, args.rules)
        print_report(report)
        all_audit.extend(audit_log)

    if args.audit_out:
        Path(args.audit_out).write_text(json.dumps(all_audit, indent=2))
        print(f"\nFull audit log ({len(all_audit)} entries) written to {args.audit_out}")


if __name__ == "__main__":
    main()
