# =========================
# Extracts skills from resume and JD
# JD   → ESCO taxonomy (explicit skill names)
# Resume → ESCO + spaCy (explicit + implied skills)
# =========================

import pandas as pd
import spacy
import os

# ─────────────────────────────────────────
# Load ESCO Skills Dataset
# ─────────────────────────────────────────

ESCO_PATH = os.path.join("data", "skills_en.csv")

def load_esco_skills():
    """
    Loads ESCO skills from CSV.
    Falls back to a basic skill list if file not found.
    """
    try:
        df = pd.read_csv(ESCO_PATH)
        skills = df["preferredLabel"].str.lower().tolist()
        print(f"✅ ESCO skills loaded: {len(skills)} skills")
        return skills

    except FileNotFoundError:
        print("⚠️ ESCO file not found. Using fallback skill list.")
        return [
            "python", "sql", "excel", "power bi", "tableau",
            "data analysis", "data visualization", "machine learning",
            "statistics", "communication", "stakeholder management",
            "reporting", "data science", "deep learning", "nlp",
            "natural language processing", "java", "javascript",
            "project management", "agile", "scrum", "aws", "azure",
            "google cloud", "docker", "kubernetes", "tensorflow",
            "pytorch", "r programming", "scala", "spark",
            "data engineering", "etl", "business intelligence"
        ]

# Load once at module level (not on every function call)
ESCO_SKILLS = load_esco_skills()


# ─────────────────────────────────────────
# Load spaCy Model
# ─────────────────────────────────────────

try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy model loaded")
except OSError:
    print("⚠️ spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


# ─────────────────────────────────────────
# Skill Extraction Functions
# ─────────────────────────────────────────

def extract_esco_skills(text):
    """
    Scans text for exact ESCO skill matches.
    Works well for JDs and resume skill sections
    because skills are explicitly named.

    Example:
        text = "We need Python and Power BI skills"
        returns → ["python", "power bi"]
    """
    text = text.lower()
    text = " ".join(text.split())  # normalize whitespace

    found = [skill for skill in ESCO_SKILLS if skill in text]
    return list(set(found))


def extract_spacy_phrases(text):
    """
    Extracts implied skills from text using spaCy noun chunks.
    Catches skills described in experience sections that
    aren't explicitly named as skills.

    Example:
        text = "Built interactive dashboards and automated workflows"
        returns → ["interactive dashboards", "automated workflows"]
    """
    if nlp is None:
        return []

    text = text.lower()
    doc = nlp(text)

    phrases = []

    # Noun chunks: "data pipelines", "interactive dashboards"
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        if len(phrase) > 2:  # ignore very short words
            phrases.append(phrase)

    # Individual key nouns
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
            if len(token.text) > 2:
                phrases.append(token.text.strip())

    return list(set(phrases))


def extract_skills(text, source="resume"):
    """
    Main skill extraction function.

    For JD:
        Uses ESCO only — JDs explicitly name required skills
        e.g. "Must have Power BI" → finds "power bi"

    For Resume:
        Uses ESCO + spaCy — resumes mix explicit and implied skills
        e.g. "Built dashboards" → ESCO misses it, spaCy catches it

    Args:
        text   : raw text string
        source : "resume" or "jd"

    Returns:
        list of skill strings
    """
    if source == "jd":
        # JDs explicitly state required skills
        # ESCO is accurate and sufficient here
        skills = extract_esco_skills(text)

    elif source == "resume":
        # Resumes mix explicit skills (skills section)
        # and implied skills (experience section)
        esco_skills  = extract_esco_skills(text)
        spacy_skills = extract_spacy_phrases(text)

        # Combine both
        skills = list(set(esco_skills + spacy_skills))

    else:
        skills = extract_esco_skills(text)

    # Final clean — remove empty strings
    skills = [s.strip() for s in skills if s.strip()]

    return skills