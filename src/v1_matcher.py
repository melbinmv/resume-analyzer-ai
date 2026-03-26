import spacy

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text)

    keywords = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            keywords.append(token.text.lower())

    return list(set(keywords))

def match_keywords(resume_keywords, job_keywords):

    matched = set(resume_keywords).intersection(set(job_keywords))

    return {
        "matched": list(matched),
        "missing": list(set(job_keywords) - set(resume_keywords))
    }

def calculate_score_v1(matched, job_keywords, important_skills=None):
    important_skills = [s.lower() for s in (important_skills or [])]
    bonus     = sum(1 for s in matched if s in important_skills)
    raw_score = ((len(matched) + bonus) / max(len(job_keywords), 1)) * 100
    score     = round(min(raw_score, 100), 2)
    return {
        "ats_score"    : score,
        "matched_count": len(matched),
        "bonus"        : bonus,
        "matched"      : matched,
        "missing"      : list(set(job_keywords) - set(matched))
    }

def run_v1(resume_text, jd_text, important_skills=None):
    resume_keywords = extract_keywords(resume_text)
    job_keywords    = extract_keywords(jd_text)
    match_result    = match_keywords(resume_keywords, job_keywords)
    score_data      = calculate_score_v1(
        match_result["matched"],
        job_keywords,
        important_skills
    )
    return {
        "resume_keywords": resume_keywords,
        "job_keywords"   : job_keywords,
        "matched"        : match_result["matched"],
        "missing"        : match_result["missing"],
        "score_data"     : score_data
    }