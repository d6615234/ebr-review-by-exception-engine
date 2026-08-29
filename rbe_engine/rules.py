"""
rules.py — the rule type registry.

Each rule TYPE is a small function with the signature
    (step: dict, params: dict) -> str | None
returning a human-readable reason string when the rule trips, or None
when the step passes that rule. New rule types are added by writing one
function and registering it in RULE_REGISTRY — nothing else in the
engine needs to change.
"""


def tolerance_check(step, params):
    """Flags when actual_value is outside +/- tolerance_pct of target_value.
    tolerance_pct can come from the step itself, or be overridden by the
    rule's own params (params wins if present, so a rule config can
    enforce a stricter tolerance than the step nominally allows)."""
    target = step.get("target_value")
    actual = step.get("actual_value")
    if target is None or actual is None:
        return None
    tol_pct = params.get("tolerance_pct", step.get("tolerance_pct", 5.0))
    tol = tol_pct / 100.0
    low, high = target * (1 - tol), target * (1 + tol)
    if not (low <= actual <= high):
        return f"actual {actual} outside [{low:.3f}, {high:.3f}] ({tol_pct}% of target {target})"
    return None


def equipment_status_check(step, params):
    """Flags when the step's recorded equipment_status is in a configured
    blocklist (default: DOWN, DISCONFIGURED)."""
    blocked = set(params.get("blocked_statuses", ["DOWN", "DISCONFIGURED"]))
    status = step.get("equipment_status")
    if status in blocked:
        return f"equipment_status={status} is a blocked status ({sorted(blocked)})"
    return None


def comment_present(step, params):
    """Flags when the operator left any free-text comment on the step."""
    comment = step.get("comment")
    if comment:
        return f"operator comment present: {comment!r}"
    return None


def value_range(step, params):
    """Flags when a named value in step['tags'][tag] falls outside
    [min, max]. Used for historian-style readings attached to a step."""
    tag = params["tag"]
    lo, hi = params.get("min"), params.get("max")
    value = (step.get("tags") or {}).get(tag)
    if value is None:
        return None
    if lo is not None and value < lo:
        return f"tag {tag}={value} below min {lo}"
    if hi is not None and value > hi:
        return f"tag {tag}={value} above max {hi}"
    return None


def duration_check(step, params):
    """Flags when a step's start/end timestamps (ISO 8601) span more
    than max_minutes."""
    from datetime import datetime
    start, end = step.get("start_time"), step.get("end_time")
    if not start or not end:
        return None
    fmt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    fmt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    minutes = (fmt_end - fmt_start).total_seconds() / 60
    max_minutes = params["max_minutes"]
    if minutes > max_minutes:
        return f"step duration {minutes:.1f} min exceeds max {max_minutes} min"
    return None


def segregation_of_duties(step, params):
    """Flags when the same user both performed and reviewed a step —
    a common GxP control that RBE rule sets are expected to enforce."""
    performed_by = step.get("performed_by")
    reviewed_by = step.get("reviewed_by")
    if performed_by and reviewed_by and performed_by == reviewed_by:
        return f"performed_by and reviewed_by are the same user ({performed_by})"
    return None


RULE_REGISTRY = {
    "tolerance_check": tolerance_check,
    "equipment_status_check": equipment_status_check,
    "comment_present": comment_present,
    "value_range": value_range,
    "duration_check": duration_check,
    "segregation_of_duties": segregation_of_duties,
}
