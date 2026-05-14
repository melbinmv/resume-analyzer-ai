# src/feedback.py

import json
import os
from datetime import datetime

FEEDBACK_PATH = os.path.join("data", "feedback_log.json")


def load_feedback():
    """
    Loads existing feedback log from JSON file.
    Returns empty list if file doesn't exist yet.
    """
    if not os.path.exists(FEEDBACK_PATH):
        return []

    with open(FEEDBACK_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_feedback(log):
    """
    Saves feedback log back to JSON file.
    Creates data/ directory if it doesn't exist.
    """
    os.makedirs("data", exist_ok=True)

    with open(FEEDBACK_PATH, "w") as f:
        json.dump(log, f, indent=2)


def log_feedback(ats_score, rating, version, notes=""):
    """
    Logs a user feedback entry to JSON file.

    Args:
        ats_score : float  — score the system gave
        rating    : str    — "accurate", "too_high", or "too_low"
        version   : str    — "v1" or "v2"
        notes     : str    — optional free text

    Returns:
        the entry that was saved
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "ats_score": ats_score,
        "rating"   : rating,
        "version"  : version,
        "notes"    : notes
    }

    log = load_feedback()
    log.append(entry)
    save_feedback(log)

    return entry


def get_feedback_summary():
    """
    Returns summary counts of all feedback collected.

    Returns:
        {
            "total"       : 42,
            "accurate"    : 30,
            "too_high"    : 8,
            "too_low"     : 4,
            "accuracy_pct": 71.4
        }
    """
    log = load_feedback()

    if not log:
        return {
            "total"       : 0,
            "accurate"    : 0,
            "too_high"    : 0,
            "too_low"     : 0,
            "accuracy_pct": 0
        }

    total    = len(log)
    accurate = sum(1 for e in log if e["rating"] == "accurate")
    too_high = sum(1 for e in log if e["rating"] == "too_high")
    too_low  = sum(1 for e in log if e["rating"] == "too_low")

    return {
        "total"       : total,
        "accurate"    : accurate,
        "too_high"    : too_high,
        "too_low"     : too_low,
        "accuracy_pct": round((accurate / total) * 100, 1)
    }