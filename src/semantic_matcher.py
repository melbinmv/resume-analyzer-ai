from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Sentence transformer model loaded")


# ─────────────────────────────────────
# SKILL_SYNONYMS
# Generic only — no domain-specific tools.
# Only universal concepts that apply across ALL domains.
# ─────────────────────────────────────
SKILL_SYNONYMS = {
    # ── Universal soft skills ──────────────────────────────
    "communication": [
        "stakeholder management", "presentations", "interpersonal skills",
        "client communication", "collaboration", "public speaking",
        "written communication", "verbal communication", "reporting",
        "documentation", "policy writing", "technical writing",
    ],
    "reporting": [
        "documentation", "report writing", "dashboards", "analytics",
        "insights", "business reporting", "written communication",
        "policy writing", "technical writing", "compliance documentation",
        "security documentation",
    ],
    "leadership": [
        "team lead", "management", "mentoring", "supervising",
        "people management", "team management",
    ],
    "collaboration": [
        "teamwork", "cross-functional", "stakeholder management",
        "communication", "worked with teams",
    ],
    "problem solving": [
        "troubleshooting", "debugging", "root cause analysis",
        "analytical thinking", "critical thinking",
    ],
    "project management": [
        "agile", "scrum", "kanban", "delivery management",
        "programme management", "planning",
    ],
    "documentation": [
        "technical writing", "report writing", "policy writing",
        "compliance documentation", "security documentation",
        "reporting", "communication",
    ],

    # ── Universal technical concepts ───────────────────────
    "analysis": [
        "analytics", "data analysis", "business analysis",
        "statistical analysis", "research", "investigation",
    ],
    "testing": [
        "qa", "quality assurance", "test automation", "unit testing",
        "integration testing", "validation", "verification",
    ],
    "architecture": [
        "system design", "infrastructure", "design patterns",
        "solution design", "technical design",
    ],
    "automation": [
        "scripting", "orchestration", "ci/cd", "devops",
        "infrastructure as code", "scheduling",
    ],
    "monitoring": [
        "observability", "alerting", "logging", "event monitoring",
        "performance monitoring", "security monitoring",
    ],
    "security": [
        "cybersecurity", "information security", "infosec",
        "network security", "application security",
    ],
    "compliance": [
        "auditing", "governance", "risk management",
        "regulatory", "compliance documentation",
    ],
    # FIX: added "audit preparation" and "compliance"
    "risk assessment": [
        "risk management", "risk analysis", "threat assessment",
        "vulnerability assessment", "auditing",
        "audit preparation", "compliance",
    ],
    "vulnerability assessment": [
        "vulnerability scanning", "vulnerability management",
        "security scanning",
    ],

    # ── Cloud — specific to actual cloud evidence only ─────
    # "infrastructure security" deliberately excluded —
    # on-premise infrastructure ≠ cloud security
    "cloud security": [
        "aws security", "azure security", "gcp security",
        "cloud infrastructure", "cloud architecture",
        "aws", "azure", "gcp",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud",
        "cloud infrastructure", "cloud security",
    ],

    # ── DevOps / engineering ───────────────────────────────
    "devops": [
        "devsecops", "ci/cd", "automation", "infrastructure as code",
        "site reliability", "sre",
    ],
    "devsecops": [
        "devops", "security automation", "ci/cd", "secure sdlc",
    ],
    "networking": [
        "network security", "firewalls", "ids/ips", "tcp/ip",
        "network administration", "infrastructure",
    ],

    # ── Programming / scripting ────────────────────────────
    "scripting": [
        "automation", "python", "bash", "powershell",
        "shell scripting", "coding", "programming",
    ],
    "programming": [
        "software development", "coding", "scripting",
        "software engineering", "development",
    ],

    # ── Data ───────────────────────────────────────────────
    "data analysis": [
        "analytics", "analysis", "data analytics",
        "business analysis", "statistical analysis", "reporting",
    ],
    "data visualization": [
        "visualization", "dashboards", "charts",
        "data viz", "reporting", "analytics",
    ],
    "machine learning": [
        "ml", "predictive modelling", "ai", "artificial intelligence",
        "deep learning", "neural networks", "statistical modelling",
    ],
    "statistical analysis": [
        "statistics", "statistical modelling",
        "data analysis", "quantitative analysis",
    ],
    "etl": [
        "data pipeline", "data engineering",
        "data integration", "data processing",
    ],
}


def get_synonym_boost(jd_skill, resume_skill, base_score):
    jd_lower     = jd_skill.lower()
    resume_lower = resume_skill.lower()

    synonyms = SKILL_SYNONYMS.get(jd_lower, [])
    if resume_lower in synonyms:
        boosted = max(base_score, 0.65)
        if boosted != base_score:
            print(f"🔗 Synonym boost: '{jd_skill}' ↔ '{resume_skill}' "
                  f"{base_score:.3f} → {boosted:.3f}")
        return boosted

    reverse_synonyms = SKILL_SYNONYMS.get(resume_lower, [])
    if jd_lower in reverse_synonyms:
        boosted = max(base_score, 0.65)
        if boosted != base_score:
            print(f"🔗 Reverse synonym boost: '{jd_skill}' ↔ '{resume_skill}' "
                  f"{base_score:.3f} → {boosted:.3f}")
        return boosted

    return base_score


# ─────────────────────────────────────
# MATCH_BLOCKLIST
# FIX: prevents semantically plausible but factually wrong matches.
# e.g. "cloud security" → "security+" scores 0.6184 via transformer
#      alone — blocked here because a cert ≠ cloud experience.
#
# Design principle:
#   Only block pairs where the match would be actively misleading.
#   Don't block just because the match is imperfect.
# ─────────────────────────────────────

MATCH_BLOCKLIST = {
    "cloud security": [
        "security+", "security policy", "security hardening",
        "network security", "information security", "cyber security",
    ],
    "penetration testing": [
        "security policy", "security hardening", "security+",
        "security monitoring", "network security",
    ],
    "devops": [
        "security policy", "security hardening", "security+",
    ],
    "devsecops": [
        "security policy", "security hardening", "security+",
    ],
    # ADD THESE:
    "communication": [
        "cyber security", "network security", "incident response",
        "vulnerability scanning", "security monitoring",
    ],
    "reporting": [
        "incident response", "cyber security", "network security",
        "vulnerability scanning", "security monitoring",
    ],
}


# ─────────────────────────────────────
# NOISE_FILTER
# All patterns anchored — no unanchored digit patterns
# that could match inside valid skill names like "iso 27001"
# ─────────────────────────────────────
NOISE_PATTERNS = [
    r"^\d+$",
    r"^[\d\s]+$",
    r"@",
    r"^(the|a|an|of|in|at|to|for|and|or|but|with|from|by)$",
    r"^.{1,2}$",
    r"(ltd|llc|inc|corp|plc)$",
    r"^(january|february|march|april|may|june|july|"
    r"august|september|october|november|december)$",
    r"^\+\d",
    r"^(bsc|msc|ba|ma|phd|hnd)$",
    r"●",
    r"^(phone|email|address|linkedin|github|twitter)$",
    r"\w+\.\w+@\w+",
    r"^(university|college|institute|school)$",
]


def is_noise(skill):
    skill = skill.strip().lower()
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, skill):
            return True
    return False


def clean_skills(skills):
    cleaned = []
    for s in skills:
        s = s.strip()
        if not s:
            continue
        if is_noise(s):
            print(f"🚫 Noise filtered: '{s}'")
            continue
        if len(s.split()) > 4:
            continue
        cleaned.append(s)
    return cleaned


# ─────────────────────────────────────
# TEXT SCAN FALLBACK
# Dynamic by default — if no hardcoded entry exists, scans
# for the skill string itself. Works for any domain.
# ─────────────────────────────────────
SURFACE_FORM_OVERRIDES = {
   "communication": [
        "communicated", "communication", "presented", "presenting",
        "stakeholders", "collaborated", "collaboration",
        "written", "verbal", "documentation", "reported",
        "policy writing", "technical writing",
        "wrote", "security policies", "playbooks",
    ],
    "reporting": [
        "reports", "reporting", "documented", "documentation",
        "dashboards", "insights", "wrote", "written",
        "policy writing", "compliance documentation",
        "security documentation", "playbooks", "audit",
    ],
    "leadership": [
        "led", "lead", "managed", "supervised",
        "headed", "mentored", "directed",
    ],
    "collaboration": [
        "collaborated", "worked with", "cross-functional",
        "partnered", "coordinated", "teamwork",
    ],
    "problem solving": [
        "solved", "resolved", "identified", "improved",
        "troubleshot", "debugged", "investigated",
    ],
    "risk assessment": [
        "risk", "assessed", "assessment", "audit",
        "audited", "evaluated", "audit preparation",
    ],
    "stakeholder management": [
        "stakeholders", "clients", "partners",
        "communicated", "presented", "collaborated",
    ],
    "documentation": [
        "documented", "wrote", "written", "reports",
        "policies", "playbooks", "runbooks",
    ],
}


def scan_resume_for_jd_skill(jd_skill, resume_text):
    resume_lower = resume_text.lower()
    scan_terms   = SURFACE_FORM_OVERRIDES.get(
        jd_skill.lower(),
        [jd_skill.lower()]
    )
    for term in scan_terms:
        if re.search(rf"\b{re.escape(term)}\b", resume_lower):
            print(f"📝 Text scan: '{jd_skill}' found via '{term}'")
            return True
    return False


# ─────────────────────────────────────
# PER-SKILL THRESHOLD OVERRIDES
# Lower threshold for soft skills only — never for tools
# ─────────────────────────────────────
SKILL_THRESHOLDS = {
    "communication"         : 0.50,
    "collaboration"         : 0.50,
    "leadership"            : 0.50,
    "teamwork"              : 0.50,
    "problem solving"       : 0.50,
    "stakeholder management": 0.50,
    "reporting"             : 0.50,
    "documentation"         : 0.50,
    "project management"    : 0.50,
}


def get_best_match(jd_skill, resume_skills, resume_embeddings):
    """
    Applies synonym boost to ALL resume skills before selecting best.
    Blocks known false-positive pairings via MATCH_BLOCKLIST.
    """
    jd_embedding = model.encode([jd_skill])
    scores       = cosine_similarity(jd_embedding, resume_embeddings)[0]
    blocklist    = MATCH_BLOCKLIST.get(jd_skill.lower(), [])

    boosted_scores = []
    for skill, score in zip(resume_skills, scores):
        if skill.lower() in blocklist:
            boosted_scores.append(0.0)
            continue
        boosted = get_synonym_boost(jd_skill, skill, float(score))
        boosted_scores.append(boosted)

    best_idx   = int(np.argmax(boosted_scores))
    best_score = boosted_scores[best_idx]
    best_skill = resume_skills[best_idx]

    return best_skill, best_score


def semantic_match(resume_skills, job_skills, threshold=0.55, resume_text=""):
    if not resume_skills or not job_skills:
        return []

    resume_skills = clean_skills(resume_skills)
    if not resume_skills:
        return []

    resume_embeddings = model.encode(resume_skills)
    results           = []

    for jd_skill in job_skills:
        best_skill, best_score = get_best_match(
            jd_skill,
            resume_skills,
            resume_embeddings
        )

        effective_threshold = SKILL_THRESHOLDS.get(
            jd_skill.lower(), threshold
        )

        if best_score >= 0.90:
            match_type = "exact"
        elif best_score >= 0.70:
            match_type = "strong"
        elif best_score >= effective_threshold:
            match_type = "partial"
        else:
            if resume_text and scan_resume_for_jd_skill(jd_skill, resume_text):
                match_type  = "partial"
                best_score  = max(best_score, effective_threshold)
                best_skill  = f"[inferred from text]"   # ← honest label
                print(f"📝 '{jd_skill}' rescued by text scan → partial")
            else:
                match_type = "none"

        results.append({
            "jd_skill"    : jd_skill,
            "resume_match": best_skill if match_type != "none" else None,
            "similarity"  : round(best_score, 4),
            "match_type"  : match_type,
            "matched"     : match_type != "none"
        })

    return results


def calculate_score(match_results, job_skills, important_skills=None):
    if not match_results:
        return {"ats_score": 0, "breakdown": []}

    important_skills = [s.lower() for s in (important_skills or [])]

    tier_weights = {
        "exact"  : 1.00,
        "strong" : 0.85,
        "partial": 0.60,
        "none"   : 0.00
    }

    IMPORTANCE_MULTIPLIER = 1.5
    total_weight          = 0
    max_weight            = 0
    breakdown             = []

    for result in match_results:
        base_weight    = tier_weights[result["match_type"]]
        is_important   = result["jd_skill"].lower() in important_skills
        multiplier     = IMPORTANCE_MULTIPLIER if is_important else 1.0
        weighted_score = base_weight * multiplier
        max_possible   = 1.0 * multiplier

        total_weight += weighted_score
        max_weight   += max_possible

        breakdown.append({
            **result,
            "is_important"  : is_important,
            "weighted_score": round(weighted_score, 4),
        })

    raw_score = (total_weight / max_weight) * 100 if max_weight > 0 else 0
    ats_score = round(min(raw_score, 100), 2)

    return {
        "ats_score"   : ats_score,
        "total_weight": round(total_weight, 4),
        "max_weight"  : round(max_weight, 4),
        "breakdown"   : breakdown
    }