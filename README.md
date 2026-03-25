# AI Resume Analyzer

An ATS (Applicant Tracking System) simulator that evaluates 
resumes against job descriptions using NLP and semantic matching.

## Versions
- **Version 1** — Rule-based keyword matching
- **Version 2** — Semantic matching using ESCO + spaCy + Sentence Transformers ← current

## Tech Stack
- Python
- Streamlit
- Sentence Transformers (all-MiniLM-L6-v2)
- ESCO Skills Taxonomy
- spaCy
- pdfplumber

## Setup

### 1. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

### 2. Download ESCO dataset
Go to: https://esco.ec.europa.eu/en/use-esco/download
Download: skills_en.csv
Save to:  data/skills_en.csv

### 3. Run the app
streamlit run app.py

## Project Structure
ats_analyzer/
├── app.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── KNOWN_ISSUES.md
├── data/
│   └── skills_en.csv
├── src/
│   ├── __init__.py
│   ├── parser.py
│   ├── skill_extractor.py
│   └── semantic_matcher.py
└── utils/
    ├── __init__.py
    └── helpers.py

## How It Works
1. Resume PDF is uploaded and text is extracted
2. Skills are extracted from resume and JD
3. Semantic similarity is calculated using embeddings
4. ATS score is calculated with weighted tiers
5. Matched and missing skills are displayed

## ATS Score Ranges
| Score   | Decision                        |
|---------|---------------------------------|
| 80-100% | Strong Match — likely shortlist |
| 65-79%  | Good Match — may pass ATS       |
| 50-64%  | Weak Match — likely filtered    |
| Below 50| Poor Match — likely rejected    |