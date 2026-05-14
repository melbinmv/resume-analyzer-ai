from google import genai
from google.genai import types
import json
import re
import os
import hashlib
import spacy
from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = "models/gemma-4-26b-a4b-it"
GEMINI_FALLBACK_MODEL = "gemini-1.5-flash"


def initialise_gemini(api_key):
    try:
        client = genai.Client(api_key=api_key)
        print(f"✅ Gemini client created — model: {GEMINI_MODEL}")
        return client
    except Exception as e:
        print(f"❌ Gemini init failed: {e}")
        return None


# ─────────────────────────────────────
# Lazy initialisation — client created on first use,
# not at module import. Sidebar key injection works correctly.
# ─────────────────────────────────────
gemini_client = None


def get_gemini_client():
    global gemini_client
    if gemini_client is not None:
        return gemini_client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  No Gemini API key found")
        return None
    gemini_client = initialise_gemini(api_key)
    return gemini_client


try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy model loaded")
except OSError:
    print("⚠️  spaCy not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


# ─────────────────────────────────────
# In-memory cache — eliminates repeat Gemini calls for the
# same resume/JD during a session. Resets on app restart.
# ─────────────────────────────────────
_extraction_cache = {}

def get_cache_key(text, source):
    return hashlib.md5(f"{source}:{text}".encode()).hexdigest()


def get_cache(cache_key):
    """Retrieve cached extraction from Streamlit session state."""
    try:
        import streamlit as st
        full_key = f"skill_cache_{cache_key}"
        return st.session_state.get(full_key)
    except RuntimeError:
        # Called outside Streamlit context (testing)
        return None


def set_cache(cache_key, value):
    """Store extraction result in Streamlit session state."""
    try:
        import streamlit as st
        full_key = f"skill_cache_{cache_key}"
        st.session_state[full_key] = value
    except RuntimeError:
        # Called outside Streamlit context — skip caching
        pass




def clean_text_for_extraction(text):
    text = re.sub(r"[●•\*\-\>·]\s*", " ", text)
    text = text.replace("\n", " ")
    text = re.sub(r"[^\w\s,.\(\)/\+\#]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_prompt(text, source):
    if source == "jd":
        return f"""
Extract all skills from this job description.
Include: technical skills, tools, frameworks, soft skills, certifications.
Normalise certs to short forms: "CompTIA Security+" → "security+", "AWS Certified" → "aws".
Lowercase, 1-3 words max, no job titles, no company names, no duplicates.
Return ONLY: {{"skills": ["python", "sql", "security+"]}}

Job Description:
{text}
"""
    else:
        return f"""
Extract ALL skills from this resume — explicit and implied from experience.
Include skills from: skills, experience, summary, projects, certifications, education.
Normalise certs: "CompTIA Security+" → "security+", "AWS Certified" → "aws", "PMP" → "project management".
Implied: "built dashboards" → "reporting", "responded to incidents" → "incident response".
Lowercase, 1-3 words max, no names/titles/dates, no duplicates.
Return ONLY: {{"skills": ["python", "sql", "security+"]}}

Resume:
{text}
"""


def parse_gemini_response(raw):
    raw = raw.strip()
    raw = re.sub(r"```[a-zA-Z]*\n?", "", raw).strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        print(f"⚠️  No JSON object found in response: {raw[:200]}")
        return []

    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON decode failed: {e} | raw snippet: {raw[:200]}")
        return []

    skills = parsed.get("skills", [])
    return [s.strip().lower() for s in skills if s.strip()]


# ─────────────────────────────────────
# SKILL_EXPANSIONS
# Resume-side: expands extracted resume skills to canonical forms.
# Handles implied skills and cert normalisation.
# ─────────────────────────────────────
SKILL_EXPANSIONS = {
    # Data
    "reports"              : ["reporting"],
    "dashboards"           : ["reporting", "data visualization"],
    "excel"                : ["spreadsheets"],
    "statistical models"   : ["statistics", "statistical modelling"],
    "statistical analysis" : ["statistics"],
    "business intelligence": ["reporting", "dashboards"],
    "data visualization"   : ["reporting", "dashboards"],
    "trend analysis"       : ["data analysis", "analytics"],
    "insights"             : ["data analysis", "reporting"],
    "machine learning"     : ["python", "statistical modelling"],
    "decision-making"      : ["analytical skills"],
    "stakeholders"         : ["communication", "stakeholder management"],

    # Security cert normalisation
    "comptia security+"                  : ["security+"],
    "comptia security plus"              : ["security+"],
    "comptia"                            : ["security+"],
    "security plus"                      : ["security+"],
    "certified ethical hacker"           : ["ceh"],
    "certified information systems security professional": ["cissp"],

    # Cloud cert normalisation
    "aws certified"                      : ["aws"],
    "aws solutions architect"            : ["aws", "cloud architecture"],
    "aws certified developer"            : ["aws"],
    "azure certified"                    : ["azure"],
    "google certified"                   : ["gcp"],
    "google professional"                : ["gcp"],
    "gcp certified"                      : ["gcp"],
    "cloud practitioner"                 : ["aws", "cloud"],

    # Project / process cert normalisation
    "pmp"                                : ["project management"],
    "prince2"                            : ["project management"],
    "certified scrum master"             : ["scrum", "agile"],
    "csm"                                : ["scrum"],

    # Data cert normalisation
    "google data engineer"               : ["data engineering", "gcp"],
    "databricks certified"               : ["spark", "data engineering"],
    "tableau desktop certified"          : ["tableau"],
    "microsoft certified"                : ["azure"],
}


# ─────────────────────────────────────
# JD_SKILL_NORMALISATIONS
# FIX: JD-side normalisation so cert names extracted from JDs
# match the canonical forms extracted from resumes.
# e.g. Gemini extracts "comptia security+" from JD →
#      normalised to "security+" → matches resume's "security+"
# ─────────────────────────────────────
JD_SKILL_NORMALISATIONS = {
    "comptia security+"                  : "security+",
    "comptia security plus"              : "security+",
    "comptia"                            : "security+",
    "security plus"                      : "security+",
    "certified ethical hacker"           : "ceh",
    "certified information systems security professional": "cissp",
    "aws certified solutions architect"  : "aws",
    "aws certified"                      : "aws",
    "azure certified"                    : "azure",
    "microsoft azure"                    : "azure",
    "google certified"                   : "gcp",
    "google cloud"                       : "gcp",
    "pmp certified"                      : "project management",
    "project management professional"    : "project management",
    "certified scrum master"             : "scrum",
}


def normalise_jd_skills(skills):
    """
    Normalise JD skill names to canonical forms so they match
    resume extractions correctly.
    """
    normalised = []
    for skill in skills:
        mapped = JD_SKILL_NORMALISATIONS.get(skill.lower(), skill)
        if mapped != skill:
            print(f"🔄 JD normalisation: '{skill}' → '{mapped}'")
        normalised.append(mapped)
    # Deduplicate preserving order
    seen = set()
    result = []
    for s in normalised:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def expand_skills(skills):
    expanded = list(skills)
    for skill in skills:
        skill_lower = skill.lower()
        additions   = SKILL_EXPANSIONS.get(skill_lower, [])
        for addition in additions:
            if addition not in expanded:
                print(f"🔄 Skill expansion: '{skill}' → adding '{addition}'")
                expanded.append(addition)
    return list(set(expanded))


def extract_noun_phrases(text):
    """
    Extract candidate skill terms from any text using spaCy.
    Used by the fallback when Gemini is unavailable.
    """
    if nlp is None:
        return []

    GENERIC_WORDS = {
        "experience", "knowledge", "skills", "ability", "role",
        "team", "company", "work", "year", "day", "time", "use",
        "way", "part", "place", "people", "person", "thing",
        "requirement", "responsibility", "opportunity", "position",
    }

    doc   = nlp(text[:5000])
    terms = []

    for token in doc:
        if (token.pos_ in ["NOUN", "PROPN"]
                and len(token.text) > 2
                and token.text.lower() not in GENERIC_WORDS):
            terms.append(token.text.lower())

    for chunk in doc.noun_chunks:
        phrase = chunk.text.lower().strip()
        if 2 <= len(phrase.split()) <= 3:
            if not any(w in phrase for w in [
                "experience", "knowledge", "ability",
                "responsibility", "requirement", "role",
            ]):
                terms.append(phrase)

    return list(set(terms))


def extract_skills_fallback(text, jd_text=""):
    """
    Dynamic fallback — builds candidate skill list from the JD itself.
    Only called when Gemini is genuinely unavailable.
    """
    print("⚠️  Using dynamic fallback — Gemini unavailable")

    jd_terms = extract_noun_phrases(jd_text) if jd_text else []

    core_skills = [
        "python", "sql", "java", "javascript", "r", "bash",
        "powershell", "scala", "go",
        "excel", "communication", "reporting", "analysis",
        "git", "agile", "scrum", "docker", "aws", "azure", "gcp",
        "linux", "windows", "networking",
        "machine learning", "statistics", "management",
        "splunk", "nmap", "nessus", "wireshark",
        "firewalls", "ids/ips", "siem", "iso 27001",
        "incident response", "security+",
    ]

    all_candidates = list(set(core_skills + jd_terms))

    # Scan original text — not cleaned — to preserve capitalised tool names
    text_lower = text.lower()
    found      = []
    for skill in all_candidates:
        pattern = rf"\b{re.escape(skill.lower())}\b"
        if re.search(pattern, text_lower):
            found.append(skill.lower())

    print(f"📋 Dynamic fallback found {len(found)} skills: {found}")
    return found


def extract_skills_gemini(text, source="resume"):
    cache_key = get_cache_key(text, source)
    cached    = get_cache(cache_key)
    if cached is not None:
        print(f"📦 Cache hit for {source} — skipping Gemini call")
        return cached

    client = get_gemini_client()

    if client is None:
        print(f"⚠️  Gemini not available — using fallback for {source}")
        return extract_skills_fallback(text)

    if not text.strip():
        return []

    print(f"🔄 Calling Gemini for {source} ({len(text)} chars)...")
    prompt = build_prompt(text, source)

    # Try primary model, fall back to secondary on quota exhaustion
    models_to_try = [GEMINI_MODEL, GEMINI_FALLBACK_MODEL]

    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an expert ATS system. "
                        "Always return valid JSON and nothing else."
                    ),
                    temperature=0,
                    max_output_tokens=256
                )
            )

            raw = response.text
            print(f"🔍 FULL RAW RESPONSE:\n{raw}\n---END---")

            skills = parse_gemini_response(raw)
            print(f"✅ Extracted {len(skills)} skills from {source} "
                  f"using {model}: {skills}")

            if source == "resume":
                skills = expand_skills(skills)
                print(f"✅ After expansion: {len(skills)} skills")
            elif source == "jd":
                skills = normalise_jd_skills(skills)
                print(f"✅ After JD normalisation: {len(skills)} skills")

            # Store in cache
            set_cache(cache_key, skills)
            return skills

        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                print(f"⚠️  {model} quota exhausted — trying next model")
                continue
            elif "500" in err or "INTERNAL" in err:
                print(f"⚠️  {model} server error — trying next model")
                continue
            else:
                print(f"⚠️  Gemini error: {type(e).__name__}: {e}")
                break

    print("⚠️  All models exhausted — using fallback")
    return extract_skills_fallback(
        text, jd_text=text if source == "jd" else ""
    )


def get_extractable_text(sections):
    include = [
        "summary", "skills", "experience",
        "projects", "certifications", "education",
    ]
    parts = []
    for s in include:
        if s in sections and sections[s].strip():
            cleaned = clean_text_for_extraction(sections[s])
            parts.append(f"=== {s.upper()} SECTION ===\n{cleaned}")
    return "\n\n".join(parts)


def extract_skills(text, source="resume", sections=None):
    if source == "resume":
        raw   = get_extractable_text(sections) if sections else text
        clean = clean_text_for_extraction(raw)
        return extract_skills_gemini(clean, source="resume")
    elif source == "jd":
        clean = clean_text_for_extraction(text)
        return extract_skills_gemini(clean, source="jd")
    else:
        clean = clean_text_for_extraction(text)
        return extract_skills_gemini(clean, source="resume")


CRITICAL_SIGNALS = [
    "must have", "must-have", "required", "essential",
    "mandatory", "you must", "we require", "critical",
    "minimum requirement", "non-negotiable"
]

LOW_PRIORITY_SIGNALS = [
    "nice to have", "nice-to-have", "preferred",
    "desirable", "bonus", "advantageous", "ideally",
    "not essential", "would be great"
]


def detect_important_skills(jd_text, extracted_jd_skills):
    jd_lower  = jd_text.lower()
    sentences = re.split(r"[.\n!?]", jd_lower)

    critical_skills  = []
    preferred_skills = []

    for sentence in sentences:
        sentence     = sentence.strip()
        is_critical  = any(sig in sentence for sig in CRITICAL_SIGNALS)
        is_preferred = any(sig in sentence for sig in LOW_PRIORITY_SIGNALS)

        for skill in extracted_jd_skills:
            if skill.lower() in sentence:
                if is_critical:
                    critical_skills.append(skill)
                elif is_preferred:
                    preferred_skills.append(skill)

    critical_set  = set(critical_skills)
    preferred_set = set(preferred_skills)
    standard      = [
        s for s in extracted_jd_skills
        if s not in critical_set and s not in preferred_set
    ]

    return {
        "critical" : list(set(critical_skills)),
        "preferred": list(set(preferred_skills)),
        "standard" : standard
    }