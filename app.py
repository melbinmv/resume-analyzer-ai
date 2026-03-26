# =========================
# 📁 app.py
# =========================

import streamlit as st
import pandas as pd

from src.parser           import extract_text_from_pdf
from src.skill_extractor  import extract_skills
from src.semantic_matcher import semantic_match, calculate_score
from src.v1_matcher       import run_v1
from utils.helpers        import (
    get_score_color,
    get_score_label,
    format_breakdown_table
)

# ─────────────────────────────────────
# Page Config
# ─────────────────────────────────────

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume Analyzer")

# ─────────────────────────────────────
# Sidebar
# ─────────────────────────────────────

st.sidebar.header("⚙️ Settings")

version = st.sidebar.radio(
    label="Select Version",
    options=[
        "Version 1 — Rule Based",
        "Version 2 — Semantic Matching",
        "Compare Both"
    ],
    index=1
)

st.sidebar.divider()

if version != "Version 1 — Rule Based":
    threshold = st.sidebar.slider(
        label="Similarity Threshold (V2)",
        min_value=0.40,
        max_value=0.85,
        value=0.55,
        step=0.05,
        help="Minimum similarity score to count as a match"
    )
else:
    threshold = 0.55

important_skills_input = st.sidebar.text_input(
    label="Important Skills (comma separated)",
    value="python, sql, power bi",
    help="These skills get extra weight in scoring"
)

show_debug = st.sidebar.checkbox("Show Debug Info", value=False)

important_skills = [
    s.strip().lower()
    for s in important_skills_input.split(",")
    if s.strip()
]

# ─────────────────────────────────────
# Version Banner
# ─────────────────────────────────────

if version == "Version 1 — Rule Based":
    st.info(
        "**Version 1** — spaCy noun extraction + "
        "keyword matching. Fast but no semantic "
        "understanding."
    )
elif version == "Version 2 — Semantic Matching":
    st.info(
        "**Version 2** — Semantic matching using "
        "ESCO taxonomy + Sentence Transformers. "
        "Understands context and similar skills."
    )
else:
    st.info(
        "**Compare Mode** — Run both versions and "
        "see how scores differ side by side."
    )

# ─────────────────────────────────────
# Inputs
# ─────────────────────────────────────

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

# ─────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────

def run_version_1(resume_text, job_description, important_skills):
    """
    Runs Version 1 analysis using original
    spaCy noun extraction + keyword matching
    """
    return run_v1(
        resume_text,
        job_description,
        important_skills
    )


def run_version_2(resume_text, job_description, important_skills, threshold):
    """
    Runs Version 2 analysis using ESCO +
    Sentence Transformers semantic matching
    """
    resume_skills = extract_skills(resume_text,    source="resume")
    job_skills    = extract_skills(job_description, source="jd")

    match_results = semantic_match(
        resume_skills,
        job_skills,
        threshold=threshold
    )

    score_data = calculate_score(
        match_results,
        job_skills,
        important_skills=important_skills
    )

    return {
        "resume_skills": resume_skills,
        "job_skills"   : job_skills,
        "match_results": match_results,
        "score_data"   : score_data
    }


def display_v1_results(results, show_debug=False):
    """
    Displays Version 1 results
    """
    score_data = results["score_data"]
    ats_score  = score_data["ats_score"]
    color      = get_score_color(ats_score)
    label      = get_score_label(ats_score)

    st.subheader(f"{color} V1 ATS Score: {ats_score}%")
    st.caption("spaCy Noun Extraction + Keyword Matching")
    st.info(label)
    st.progress(int(ats_score))

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("✅ Matched Skills")
        if results["matched"]:
            for skill in results["matched"]:
                st.success(skill)
        else:
            st.write("No skills matched")

    with col_b:
        st.subheader("❌ Missing Skills")
        if results["missing"]:
            for skill in results["missing"]:
                st.error(skill)
        else:
            st.write("No missing skills!")

    st.divider()
    st.subheader("💡 Recommendations")

    if results["missing"]:
        st.warning(
            f"Your resume is missing "
            f"**{len(results['missing'])}** "
            f"skill(s) from the job description."
        )
        for skill in results["missing"]:
            is_important = skill.lower() in important_skills
            priority     = "🔴 Critical" if is_important else "🟠 Recommended"
            st.write(f"- **{skill}** — {priority}")
    else:
        st.success("Your resume covers all required skills! 🎉")

    if show_debug:
        st.divider()
        st.subheader("🐛 V1 Debug Info")

        with st.expander(
            f"Resume Keywords ({len(results['resume_keywords'])})"
        ):
            st.write(results["resume_keywords"])

        with st.expander(
            f"JD Keywords ({len(results['job_keywords'])})"
        ):
            st.write(results["job_keywords"])

        with st.expander("Score Calculation"):
            st.write({
                "matched_count": score_data["matched_count"],
                "bonus"        : score_data["bonus"],
                "ats_score"    : score_data["ats_score"]
            })


def display_v2_results(results, show_debug=False):
    """
    Displays Version 2 results
    """
    score_data    = results["score_data"]
    match_results = results["match_results"]
    ats_score     = score_data["ats_score"]
    color         = get_score_color(ats_score)
    label         = get_score_label(ats_score)

    st.subheader(f"{color} V2 ATS Score: {ats_score}%")
    st.caption("Semantic Matching — ESCO + Sentence Transformers")
    st.info(label)
    st.progress(int(ats_score))

    st.divider()

    st.subheader("📊 Skill Match Breakdown")
    breakdown_table = format_breakdown_table(score_data["breakdown"])
    st.dataframe(
        pd.DataFrame(breakdown_table),
        use_container_width=True
    )

    st.divider()

    col_a, col_b = st.columns(2)

    matched_skills = [
        r["jd_skill"] for r in match_results if r["matched"]
    ]
    missing_skills = [
        r["jd_skill"] for r in match_results if not r["matched"]
    ]

    with col_a:
        st.subheader("✅ Matched Skills")
        if matched_skills:
            for skill in matched_skills:
                st.success(skill)
        else:
            st.write("No skills matched")

    with col_b:
        st.subheader("❌ Missing Skills")
        if missing_skills:
            for skill in missing_skills:
                st.error(skill)
        else:
            st.write("No missing skills!")

    st.divider()
    st.subheader("💡 Recommendations")

    if missing_skills:
        st.warning(
            f"Your resume is missing "
            f"**{len(missing_skills)}** "
            f"skill(s) from the job description."
        )
        for skill in missing_skills:
            is_important = skill.lower() in important_skills
            priority     = "🔴 Critical" if is_important else "🟠 Recommended"
            st.write(f"- **{skill}** — {priority}")
    else:
        st.success("Your resume covers all required skills! 🎉")

    if show_debug:
        st.divider()
        st.subheader("🐛 V2 Debug Info")

        with st.expander("Raw Resume Text"):
            st.text(repr(results["resume_skills"]))

        with st.expander(
            f"Resume Skills ({len(results['resume_skills'])})"
        ):
            st.write(results["resume_skills"])

        with st.expander(
            f"JD Skills ({len(results['job_skills'])})"
        ):
            st.write(results["job_skills"])

        with st.expander("Score Calculation"):
            st.write({
                "total_weight": score_data["total_weight"],
                "max_weight"  : score_data["max_weight"],
                "ats_score"   : score_data["ats_score"]
            })


# ─────────────────────────────────────
# Main Analysis
# ─────────────────────────────────────

if resume_file and job_description:

    resume_text = extract_text_from_pdf(resume_file)

    st.divider()

    # ─────────────────────────────
    # VERSION 1 ONLY
    # ─────────────────────────────
    if version == "Version 1 — Rule Based":

        with st.spinner("🔍 Running Version 1 analysis..."):
            v1_results = run_version_1(
                resume_text,
                job_description,
                important_skills
            )

        display_v1_results(v1_results, show_debug)

    # ─────────────────────────────
    # VERSION 2 ONLY
    # ─────────────────────────────
    elif version == "Version 2 — Semantic Matching":

        with st.spinner("🔍 Running Version 2 analysis..."):
            v2_results = run_version_2(
                resume_text,
                job_description,
                important_skills,
                threshold
            )

        display_v2_results(v2_results, show_debug)

    # ─────────────────────────────
    # COMPARE BOTH
    # ─────────────────────────────
    elif version == "Compare Both":

        with st.spinner("🔍 Running both versions..."):
            v1_results = run_version_1(
                resume_text,
                job_description,
                important_skills
            )
            v2_results = run_version_2(
                resume_text,
                job_description,
                important_skills,
                threshold
            )

        # Score comparison banner
        v1_score = v1_results["score_data"]["ats_score"]
        v2_score = v2_results["score_data"]["ats_score"]
        diff     = round(v2_score - v1_score, 2)

        st.subheader("📊 Score Comparison")

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            st.metric(
                label="Version 1 — Rule Based",
                value=f"{v1_score}%"
            )

        with metric_col2:
            st.metric(
                label="Version 2 — Semantic",
                value=f"{v2_score}%",
                delta=f"{diff}% vs V1"
            )

        with metric_col3:
            st.metric(
                label="Improvement",
                value=f"{abs(diff)}%",
                delta=(
                    "semantic understanding"
                    if diff > 0
                    else "V1 scored higher"
                )
            )

        st.divider()

        # Side by side
        v1_col, v2_col = st.columns(2)

        with v1_col:
            st.subheader("🔵 Version 1")
            display_v1_results(v1_results, show_debug)

        with v2_col:
            st.subheader("🟢 Version 2")
            display_v2_results(v2_results, show_debug)

else:
    st.info("👆 Upload a resume and paste a job description to get started")