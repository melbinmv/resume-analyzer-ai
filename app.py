import streamlit as st
from src.parser import extract_text_from_pdf
from src.keyword_matcher import extract_keywords, match_keywords
from src.scorer import calculate_score

st.title("AI Resume Analyzer")

resume_file = st.file_uploader("Upload Resume (PDF)")

job_description = st.text_area("Paste Job Description")

if resume_file and job_description:

    resume_text = extract_text_from_pdf(resume_file)

    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)

    result = match_keywords(resume_keywords, job_keywords)

    score = calculate_score(result["matched"], len(job_keywords))

    st.subheader(f"ATS Score: {score}")

    st.write("Matched Skills:", result["matched"])
    st.write("Missing Skills:", result["missing"])