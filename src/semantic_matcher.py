# =========================
# Matches resume skills to JD skills using
# sentence embeddings and cosine similarity
# =========================

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load model once at module level
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Sentence transformer model loaded")


def get_best_match(jd_skill, resume_skills, resume_embeddings):
    """
    Finds the most semantically similar resume skill
    for a given JD skill.

    Returns:
        best_skill  : closest matching resume skill
        best_score  : similarity score (0.0 to 1.0)
    """
    jd_embedding = model.encode([jd_skill])

    # Compare JD skill against all resume skills at once
    scores = cosine_similarity(jd_embedding, resume_embeddings)[0]

    best_idx   = np.argmax(scores)
    best_score = float(scores[best_idx])
    best_skill = resume_skills[best_idx]

    return best_skill, best_score


def semantic_match(resume_skills, job_skills, threshold=0.55):
    """
    Matches each JD skill to the closest resume skill
    using semantic similarity.

    Matching tiers:
        Exact match   : similarity >= 0.90
        Strong match  : similarity >= 0.70
        Partial match : similarity >= threshold (0.55)
        No match      : similarity <  threshold

    Args:
        resume_skills : list of skills from resume
        job_skills    : list of skills from JD
        threshold     : minimum similarity to count as a match

    Returns:
        results : list of dicts with full match details
    """

    if not resume_skills or not job_skills:
        return []

    # Pre-compute all resume embeddings at once (more efficient)
    resume_embeddings = model.encode(resume_skills)

    results = []

    for jd_skill in job_skills:
        best_skill, best_score = get_best_match(
            jd_skill,
            resume_skills,
            resume_embeddings
        )

        # Determine match tier
        if best_score >= 0.90:
            match_type = "exact"
        elif best_score >= 0.70:
            match_type = "strong"
        elif best_score >= threshold:
            match_type = "partial"
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
    """
    Calculates the final ATS score from match results.

    Scoring weights:
        Exact match   → 1.00
        Strong match  → 0.85
        Partial match → 0.60
        No match      → 0.00

    Important skills get a 1.5x multiplier if matched.

    Args:
        match_results    : output from semantic_match()
        job_skills       : list of JD skills (for denominator)
        important_skills : list of high-priority skills

    Returns:
        score_data : dict with score and breakdown
    """
    if not match_results:
        return {"ats_score": 0, "breakdown": []}

    important_skills = [s.lower() for s in (important_skills or [])]

    # Weights for each match tier
    tier_weights = {
        "exact"  : 1.00,
        "strong" : 0.85,
        "partial": 0.60,
        "none"   : 0.00
    }

    # Important skill multiplier
    IMPORTANCE_MULTIPLIER = 1.5

    total_weight    = 0
    max_weight      = 0
    breakdown       = []

    for result in match_results:
        base_weight = tier_weights[result["match_type"]]

        # Apply importance multiplier if skill is important
        is_important = result["jd_skill"].lower() in important_skills
        multiplier   = IMPORTANCE_MULTIPLIER if is_important else 1.0

        weighted_score = base_weight * multiplier
        max_possible   = 1.0 * multiplier  # max score for this skill

        total_weight += weighted_score
        max_weight   += max_possible

        breakdown.append({
            **result,
            "is_important"   : is_important,
            "weighted_score" : round(weighted_score, 4),
        })

    # Normalize score to 0-100 and cap at 100
    raw_score = (total_weight / max_weight) * 100 if max_weight > 0 else 0
    ats_score = round(min(raw_score, 100), 2)

    return {
        "ats_score"   : ats_score,
        "total_weight": round(total_weight, 4),
        "max_weight"  : round(max_weight, 4),
        "breakdown"   : breakdown
    }