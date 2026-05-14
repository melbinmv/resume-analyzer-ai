# app.py

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

if "skill_cache" not in st.session_state:
    st.session_state.skill_cache = {}


from src.parser import (
    extract_text,
    extract_resume_sections,
    split_into_sections
)
from src.skill_extractor import (
    extract_skills,
    detect_important_skills
)
from src.semantic_matcher import semantic_match, calculate_score
from src.v1_matcher       import run_v1
from src.feedback         import log_feedback, get_feedback_summary
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
# Sidebar — API Key
# ─────────────────────────────────────

st.sidebar.header("⚙️ Settings")

env_key = os.getenv("GEMINI_API_KEY")

if not env_key:
    st.sidebar.subheader("🔑 Gemini API Key")
    user_key = st.sidebar.text_input(
        label="Paste API Key",
        type="password",
        placeholder="Get free key at aistudio.google.com",
        help="Get a free key at aistudio.google.com"
    )

    if user_key:
        os.environ["GEMINI_API_KEY"] = user_key
        import google.generativeai as genai
        genai.configure(api_key=user_key)
        st.sidebar.success("✅ API key set for this session")
    else:
        st.sidebar.warning(
            "⚠️ No API key — spaCy fallback will be used. "
            "Add key for better results."
        )
else:
    st.sidebar.success("✅ Gemini API key loaded from .env")

st.sidebar.divider()

# ─────────────────────────────────────
# Sidebar — Version Select
# ─────────────────────────────────────

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

# ─────────────────────────────────────
# Sidebar — Settings
# ─────────────────────────────────────

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

auto_detect_important = st.sidebar.checkbox(
    label="Auto-detect Important Skills from JD",
    value=True,
    help=(
        "Scans JD for phrases like 'must have', 'required', "
        "'essential' to automatically flag critical skills"
    )
)

if not auto_detect_important:
    important_skills_input = st.sidebar.text_input(
        label="Important Skills (comma separated)",
        value="python, sql, power bi",
        help="These skills get extra weight in scoring"
    )
    manual_important_skills = [
        s.strip().lower()
        for s in important_skills_input.split(",")
        if s.strip()
    ]
else:
    manual_important_skills = []

show_debug = st.sidebar.checkbox(
    label="Show Debug Info",
    value=False
)

st.sidebar.divider()

# ─────────────────────────────────────
# Sidebar — Feedback Summary
# ─────────────────────────────────────

st.sidebar.subheader("📊 Feedback Summary")

summary = get_feedback_summary()

if summary["total"] > 0:
    st.sidebar.metric("Total Ratings",  summary["total"])
    st.sidebar.metric("Accuracy",       f"{summary['accuracy_pct']}%")
    st.sidebar.metric("Rated Too High", summary["too_high"])
    st.sidebar.metric("Rated Too Low",  summary["too_low"])
else:
    st.sidebar.caption("No feedback recorded yet")

# ─────────────────────────────────────
# Version Banner
# ─────────────────────────────────────

if version == "Version 1 — Rule Based":
    st.info(
        "**Version 1** — spaCy noun extraction + "
        "keyword matching. Fast but no semantic understanding."
    )
elif version == "Version 2 — Semantic Matching":
    st.info(
        "**Version 2** — Gemini skill extraction + "
        "Sentence Transformer semantic matching. "
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
    resume_file = st.file_uploader(
        label="Upload PDF or DOCX",
        type=["pdf", "docx"]
    )

with col2:
    st.subheader("📋 Job Description")
    job_description = st.text_area(
        label="Paste Job Description Here",
        height=300,
        placeholder="We are looking for a Data Analyst..."
    )

# ─────────────────────────────────────
# Core Analysis Functions
# ─────────────────────────────────────

def run_version_1(resume_text, jd_text, important_skills):
    """Runs V1 — spaCy noun extraction + keyword matching."""
    return run_v1(
        resume_text,
        jd_text,
        important_skills
    )


def run_version_2(
    resume_text,
    jd_text,
    important_skills,
    threshold,
    sections=None
):
    """
    Runs V2 — Gemini skill extraction + semantic matching.

    Pipeline:
        1. Gemini extracts skills from resume (section-filtered)
        2. Gemini extracts skills from JD
        3. Auto-detect important skills from JD text
        4. Semantic matching with noise filter
        5. Weighted score calculation
    """

    # ── Skill Extraction ────────────────────────────────
    resume_skills = extract_skills(
        resume_text,
        source="resume",
        sections=sections      # header excluded if sections available
    )

    job_skills = extract_skills(
        jd_text,
        source="jd"
    )

    # ── Important Skills ─────────────────────────────────
    if auto_detect_important:
        importance_data  = detect_important_skills(jd_text, job_skills)
        important_skills = importance_data["critical"]
    else:
        importance_data  = None
        important_skills = manual_important_skills

    # ── Semantic Matching ────────────────────────────────
    match_results = semantic_match(
        resume_skills,
        job_skills,
        threshold=threshold,
        resume_text=resume_text
    )

    # ── Scoring ──────────────────────────────────────────
    score_data = calculate_score(
        match_results,
        job_skills,
        important_skills=important_skills
    )

    return {
        "resume_skills"   : resume_skills,
        "job_skills"      : job_skills,
        "match_results"   : match_results,
        "score_data"      : score_data,
        "important_skills": important_skills,
        "importance_data" : importance_data
    }


# ─────────────────────────────────────
# Display Helper Functions
# ─────────────────────────────────────

def display_feedback_widget(ats_score, version_label):
    """
    Thumbs up/down feedback widget.
    Logs rating to feedback_log.json on click.
    """
    st.divider()
    st.subheader("💬 Was this score accurate?")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("👍 Accurate", key=f"accurate_{version_label}"):
            log_feedback(ats_score, "accurate", version_label)
            st.success("Thanks for your feedback!")

    with col_b:
        if st.button("📈 Too High", key=f"too_high_{version_label}"):
            log_feedback(ats_score, "too_high", version_label)
            st.success("Thanks — we'll use this to improve!")

    with col_c:
        if st.button("📉 Too Low", key=f"too_low_{version_label}"):
            log_feedback(ats_score, "too_low", version_label)
            st.success("Thanks — we'll use this to improve!")


def display_importance_breakdown(importance_data):
    """
    Shows auto-detected skill priority tiers from JD.
    Only shown when auto-detect is enabled.
    """
    if not importance_data:
        return

    st.divider()
    st.subheader("🎯 Auto-detected Skill Priorities")
    st.caption(
        'Detected from phrases like "must have", '
        '"required", "nice to have" in the JD'
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("**🔴 Critical**")
        if importance_data["critical"]:
            for s in importance_data["critical"]:
                st.error(s)
        else:
            st.caption("None detected")

    with col_b:
        st.markdown("**🟡 Preferred**")
        if importance_data["preferred"]:
            for s in importance_data["preferred"]:
                st.warning(s)
        else:
            st.caption("None detected")

    with col_c:
        st.markdown("**🔵 Standard**")
        if importance_data["standard"]:
            for s in importance_data["standard"][:10]:
                st.info(s)
        else:
            st.caption("None detected")


def display_recommendations(missing_skills, important_skills):
    """
    Shows recommendation list for missing skills.
    Flags critical skills in red, others in orange.
    """
    st.divider()
    st.subheader("💡 Recommendations")

    if missing_skills:
        st.warning(
            f"Your resume is missing "
            f"**{len(missing_skills)}** skill(s) "
            f"from the job description."
        )
        for skill in missing_skills:
            is_important = skill.lower() in [
                s.lower() for s in important_skills
            ]
            priority = "🔴 Critical" if is_important else "🟠 Recommended"
            st.write(f"- **{skill}** — {priority}")
    else:
        st.success("Your resume covers all required skills! 🎉")


def display_v1_results(results, show_debug=False):
    """Renders full Version 1 results panel."""

    score_data = results["score_data"]
    ats_score  = score_data["ats_score"]
    color      = get_score_color(ats_score)
    label      = get_score_label(ats_score)

    # ── Score Banner ─────────────────────────────────────
    st.subheader(f"{color} V1 ATS Score: {ats_score}%")
    st.caption("spaCy Noun Extraction + Keyword Matching")
    st.info(label)
    st.progress(int(ats_score))

    st.divider()

    # ── Matched / Missing ────────────────────────────────
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

    # ── Recommendations ──────────────────────────────────
    display_recommendations(
        results["missing"],
        manual_important_skills
    )

    # ── Feedback ─────────────────────────────────────────
    display_feedback_widget(ats_score, "v1")

    # ── Debug ────────────────────────────────────────────
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
    """Renders full Version 2 results panel."""

    score_data    = results["score_data"]
    match_results = results["match_results"]
    ats_score     = score_data["ats_score"]
    color         = get_score_color(ats_score)
    label         = get_score_label(ats_score)

    # ── Score Banner ─────────────────────────────────────
    st.subheader(f"{color} V2 ATS Score: {ats_score}%")
    st.caption("Gemini Skill Extraction + Sentence Transformer Matching")
    st.info(label)
    st.progress(int(ats_score))

    # ── Auto-detected Priorities ─────────────────────────
    if auto_detect_important and results.get("importance_data"):
        display_importance_breakdown(results["importance_data"])

    st.divider()

    # ── Match Breakdown Table ────────────────────────────
    st.subheader("📊 Skill Match Breakdown")
    breakdown_table = format_breakdown_table(score_data["breakdown"])

    if breakdown_table:
        st.dataframe(
            pd.DataFrame(breakdown_table),
            use_container_width=True
        )
    else:
        st.info("No breakdown available")

    st.divider()

    # ── Matched / Missing ────────────────────────────────
    matched_skills = [
        r["jd_skill"] for r in match_results if r["matched"]
    ]
    missing_skills = [
        r["jd_skill"] for r in match_results if not r["matched"]
    ]

    col_a, col_b = st.columns(2)

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

    # ── Recommendations ──────────────────────────────────
    display_recommendations(
        missing_skills,
        results.get("important_skills", [])
    )

    # ── Feedback ─────────────────────────────────────────
    display_feedback_widget(ats_score, "v2")

    # ── Debug ────────────────────────────────────────────
    if show_debug:
        st.divider()
        st.subheader("🐛 V2 Debug Info")

        with st.expander(
            f"Resume Skills ({len(results['resume_skills'])})"
        ):
            st.write(sorted(results["resume_skills"]))

        with st.expander(
            f"JD Skills ({len(results['job_skills'])})"
        ):
            st.write(sorted(results["job_skills"]))

        with st.expander("Score Calculation"):
            st.write({
                "total_weight": score_data["total_weight"],
                "max_weight"  : score_data["max_weight"],
                "ats_score"   : score_data["ats_score"]
            })

        with st.expander("Auto-detected Important Skills"):
            st.write(results.get("importance_data", {}))

        with st.expander("Full Match Results"):
            st.write(results["match_results"])


# ─────────────────────────────────────
# Main Analysis
# ─────────────────────────────────────

if resume_file and job_description:

    # ── Extract Text and Sections ────────────────────────
    file_extension = resume_file.name.split(".")[-1].lower()

    with st.spinner("📄 Extracting text from resume..."):
        parsed      = extract_resume_sections(resume_file, file_extension)
        resume_text = parsed["full_text"]
        sections    = parsed["sections"]

    # ── Guard — empty file ───────────────────────────────
    if not resume_text.strip():
        st.error(
            "❌ Could not extract text from your file. "
            "Try a different PDF or DOCX."
        )
        st.stop()

    # ── Show detected sections ───────────────────────────
    if sections:
        detected = [s for s in sections.keys() if s != "header"]
        if detected:
            st.caption(
                f"📑 Sections detected: {', '.join(detected)}"
            )
        else:
            st.caption(
                "⚠️ No section headers detected — "
                "full text will be used for extraction"
            )

    st.divider()

    # ─────────────────────────────
    # VERSION 1 ONLY
    # ─────────────────────────────
    if version == "Version 1 — Rule Based":

        with st.spinner("🔍 Running Version 1 analysis..."):
            v1_results = run_version_1(
                resume_text,
                job_description,
                manual_important_skills
            )

        display_v1_results(v1_results, show_debug)

    # ─────────────────────────────
    # VERSION 2 ONLY
    # ─────────────────────────────
    elif version == "Version 2 — Semantic Matching":

        with st.spinner("🔍 Extracting skills and running analysis..."):
            v2_results = run_version_2(
                resume_text,
                job_description,
                manual_important_skills,
                threshold,
                sections=sections
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
                manual_important_skills
            )
            v2_results = run_version_2(
                resume_text,
                job_description,
                manual_important_skills,
                threshold,
                sections=sections
            )

        # ── Score Comparison Banner ──────────────────────
        v1_score = v1_results["score_data"]["ats_score"]
        v2_score = v2_results["score_data"]["ats_score"]
        diff     = round(v2_score - v1_score, 2)

        st.subheader("📊 Score Comparison")

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                label="Version 1 — Rule Based",
                value=f"{v1_score}%"
            )

        with m2:
            st.metric(
                label="Version 2 — Semantic",
                value=f"{v2_score}%",
                delta=f"{diff}% vs V1"
            )

        with m3:
            st.metric(
                label="Difference",
                value=f"{abs(diff)}%",
                delta=(
                    "V2 scored higher"
                    if diff > 0
                    else "V1 scored higher"
                )
            )

        st.divider()

        # ── Side by Side Results ─────────────────────────
        v1_col, v2_col = st.columns(2)

        with v1_col:
            st.subheader("🔵 Version 1 — Rule Based")
            display_v1_results(v1_results, show_debug)

        with v2_col:
            st.subheader("🟢 Version 2 — Semantic")
            display_v2_results(v2_results, show_debug)

else:
    st.info(
        "👆 Upload a resume and paste a job description to get started"
    )