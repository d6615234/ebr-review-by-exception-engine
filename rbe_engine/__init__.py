"""
rbe_engine
===========
A standalone, configuration-driven Review-by-Exception (RBE) engine for
electronic batch records.

Design goal: rules live in JSON config files, not in code. A
Configuration Lead (or anyone governing the "core model") should be able
to add, remove, or retune a rule — a tolerance percentage, a blocked
equipment status, a max step duration — by editing a JSON file and
re-running, without a code change or redeploy. That is the practical
difference between this repo and a typical if/else review script, and
it mirrors how rule-driven review actually gets configured in production
MES platforms.

Nothing here talks to a real MES, ERP, or historian system. It operates
on plain JSON batch-execution records so the engine itself is fully
testable and portable.
"""

__version__ = "0.1.0"
