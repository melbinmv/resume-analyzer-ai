# =========================
# Helper functions for displaying results
# =========================

def get_score_color(score):
    """Returns color based on ATS score range"""
    if score >= 80:
        return "🟢"
    elif score >= 65:
        return "🟡"
    elif score >= 50:
        return "🟠"
    else:
        return "🔴"


def get_score_label(score):
    """Returns decision label based on ATS score"""
    if score >= 80:
        return "Strong Match — Likely to be shortlisted ✅"
    elif score >= 65:
        return "Good Match — May pass ATS screening 🟡"
    elif score >= 50:
        return "Weak Match — Likely filtered out 🟠"
    else:
        return "Poor Match — Will likely be rejected ❌"


def get_match_emoji(match_type):
    """Returns emoji for match type"""
    return {
        "exact"  : "✅",
        "strong" : "🟢",
        "partial": "🟡",
        "none"   : "❌"
    }.get(match_type, "❓")


def format_breakdown_table(breakdown):
    """
    Formats match breakdown into a list of dicts
    for display in a Streamlit table.
    """
    rows = []
    for item in breakdown:
        rows.append({
            "JD Skill"      : item["jd_skill"],
            "Resume Match"  : item["resume_match"] or "No match found",
            "Similarity"    : f"{item['similarity']:.2f}",
            "Match Type"    : f"{get_match_emoji(item['match_type'])} {item['match_type'].title()}",
            "Important"     : "⭐" if item["is_important"] else ""
        })
    return rows