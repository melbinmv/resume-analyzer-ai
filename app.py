# =========================
# Main Streamlit application
# =========================

import streamlit as st
import pandas as pd

from src.parser           import extract_text_from_pdf
from src.skill_extractor  import extract_skills
from src.semantic_matcher import semantic_match, calculate_score
from utils.helpers        import (
    get_score_color,
    get_score_label,
    format_breakdown_table
)

# ─────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume Analyzer — Version 2")
st.caption("Semantic ATS Matching using ESCO + spaCy + Sentence Transformers")

# ─────────────────────────────────────────
# Sidebar Settings
# ─────────────────────────────────────────

st.sidebar.header("⚙️ Settings")

threshold = st.sidebar.slider(
    label="Semantic Similarity Threshold",
    min_value=0.40,
    max_value=0.85,
    value=0.55,
    step=0.05,
    help="Minimum similarity score to count as a match"
)

important_skills_input = st.sidebar.text_input(
    label="Important Skills (comma separated)",
    value="python, sql, power bi",
    help="These skills get extra weight in scoring"
)

show_debug = st.sidebar.checkbox("Show Debug Info", value=False)

# Parse important skills
important_skills = [
    s.strip().lower()
    for s in important_skills_input.split(",")
    if s.strip()
]

# ─────────────────────────────────────────
# Inputs
# ─────────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    st.subheader("📎 Upload Resume")
    resume_file = st.file_uploader("Upload PDF", type=["pdf"])

with col2:
    st.subheader("📋 Job Description")
    job_description = st.text_area(
        label="Paste Job Description Here",
        height=300,
        placeholder="We are looking for a Data Analyst..."
    )

# ─────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────

if resume_file and job_description:

    with st.spinner("🔍 Analysing resume..."):

        # Step 1: Extract raw text
        resume_text = extract_text_from_pdf(resume_file)

        # Step 2: Extract skills
        resume_skills = extract_skills(resume_text,    source="resume")
        job_skills    = extract_skills(job_description, source="jd")

        # Step 3: Semantic matching
        match_results = semantic_match(
            resume_skills,
            job_skills,
            threshold=threshold
        )

        # Step 4: Calculate score
        score_data = calculate_score(
            match_results,
            job_skills,
            important_skills=important_skills
        )

    # ─────────────────────────────────────────
    # Results Display
    # ─────────────────────────────────────────

    st.divider()

    # ATS Score
    ats_score = score_data["ats_score"]
    color     = get_score_color(ats_score)
    label     = get_score_label(ats_score)

    st.subheader(f"{color} ATS Score: {ats_score}%")
    st.info(label)
    st.progress(int(ats_score))

    st.divider()

    # Match Breakdown Table
    st.subheader("📊 Skill Match Breakdown")

    breakdown_table = format_breakdown_table(score_data["breakdown"])
    st.dataframe(
        pd.DataFrame(breakdown_table),
        use_container_width=True
    )

    st.divider()

    # Matched vs Missing
    col3, col4 = st.columns(2)

    matched_skills = [
        r["jd_skill"]
        for r in match_results
        if r["matched"]
    ]

    missing_skills = [
        r["jd_skill"]
        for r in match_results
        if not r["matched"]
    ]

    with col3:
        st.subheader("✅ Matched Skills")
        if matched_skills:
            for skill in matched_skills:
                st.success(skill)
        else:
            st.write("No skills matched")

    with col4:
        st.subheader("❌ Missing Skills")
        if missing_skills:
            for skill in missing_skills:
                st.error(skill)
        else:
            st.write("No missing skills — great match!")

    st.divider()

    # Recommendations
    st.subheader("💡 Recommendations")

    if missing_skills:
        st.warning(
            f"Your resume is missing **{len(missing_skills)}** "
            f"skill(s) from the job description."
        )
        for skill in missing_skills:
            is_important = skill.lower() in important_skills
            priority = "🔴 Critical" if is_important else "🟠 Recommended"
            st.write(f"- **{skill}** — {priority}")
    else:
        st.success("Your resume covers all required skills! 🎉")

    # Debug Section
    if show_debug:
        st.divider()
        st.subheader("🐛 Debug Info")

        with st.expander("Raw Resume Text"):
            st.text(repr(resume_text[:1000]))

        with st.expander(f"Resume Skills ({len(resume_skills)})"):
            st.write(resume_skills)

        with st.expander(f"JD Skills ({len(job_skills)})"):
            st.write(job_skills)

        with st.expander("Score Calculation"):
            st.write({
                "total_weight": score_data["total_weight"],
                "max_weight"  : score_data["max_weight"],
                "ats_score"   : score_data["ats_score"]
            })

else:
    st.info("👆 Upload a resume and paste a job description to get started")