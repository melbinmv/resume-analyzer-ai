# ATS Resume Analyser

An intelligent ATS (Applicant Tracking System) simulator that evaluates resumes against job descriptions using semantic matching with LLM-powered skill extraction.

**Current Version:** 2.1 (V2 with Gemini + Sentence Transformers)  
**Status:** Production-ready with known limitations documented

-----

## Overview

The analyser scores how well a resume matches a job description by:

1. **Extracting skills** from both resume and JD using Gemini API (with spaCy fallback)
1. **Normalising skills** (e.g., “CompTIA Security+” → “security+”)
1. **Semantic matching** using sentence transformers to find similar skills across phrasings
1. **Tiered scoring** with weighted importance for critical skills

### Dual Modes

|Mode       |Extraction                 |Matching                       |Speed        |Accuracy  |
|-----------|---------------------------|-------------------------------|-------------|----------|
|**V1**     |spaCy noun chunks          |Keyword similarity             |Fast         |~50%      |
|**V2**     |Gemini API + spaCy fallback|Sentence Transformer embeddings|Slower (2–4s)|~55–65%   |
|**Compare**|Both                       |Side-by-side metrics           |Slowest      |Diagnostic|

-----

## Features

- ✅ **LLM-Powered Extraction** – Gemini 2.0 Flash and Gemma extracts skills, certs, and implied abilities
- ✅ **Semantic Matching** – all-MiniLM-L6-v2 embeddings understand skill synonyms (“pentest” ≈ “penetration testing”)
- ✅ **Skill Normalisation** – Resume & JD side normalisation for consistent matching (AWS cert variants, PMP/Scrum, CompTIA certs)
- ✅ **Blocklist Filtering** – Prevents false positives (e.g., cloud security ≠ security+)
- ✅ **Per-Skill Thresholds** – Soft skills (0.50) vs hard skills (0.55) for realistic matching
- ✅ **Important Skills Multiplier** – Critical skills get 1.5x weight boost
- ✅ **Weighted Scoring** – Exact (1.0) / Strong (0.85) / Partial (0.60) / None (0.0)
- ✅ **Feedback Loop** – Thumbs up/down logging for model improvement
- ✅ **Debug Mode** – Raw extraction, section detection, matched/missing skills
- ✅ **Multi-Format Support** – PDF (pdfplumber) and DOCX (python-docx)

-----

## Tech Stack

```
Python 3.10+
├── Streamlit          — UI framework
├── Gemini 2.0 Flash   — LLM skill extraction (with 1.5 Flash fallback)
├── Sentence Transformers — all-MiniLM-L6-v2 semantic matching
├── spaCy              — NLP (noun chunk fallback, section detection)
├── pdfplumber         — PDF text extraction
├── python-docx        — DOCX parsing
└── google-generativeai — Gemini client
```

-----

## Installation

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd ats-analyzer
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Set Up Gemini API Key

Get a free key from [Google AI Studio](https://aistudio.google.com/):

```bash
export GOOGLE_API_KEY="your-key-here"
```

Or enter it in the Streamlit sidebar when you run the app.

### 3. Run

```bash
streamlit run app.py
```

Open <http://localhost:8501> in your browser.

-----

## How It Works

### Resume Processing

```
PDF/DOCX Upload
    ↓
Text Extraction (pdfplumber / python-docx)
    ↓
Section Detection (skills, experience, education, certs, etc.)
    ↓
Gemini Extraction (skills, certs, implied abilities)
    ├─ Fallback: spaCy noun chunks if Gemini fails/rate-limited
    └─ Result cached in session state (no re-extraction on rerun)
```

### Skill Matching

```
Resume Skills + JD Skills
    ↓
Normalisation (cert variants, tool aliases)
    ↓
Embedding Generation (Sentence Transformer)
    ↓
Cosine Similarity + Synonym Boost
    ├─ Exact match     (100% → 1.0)
    ├─ Strong match    (>0.85 cosine → 0.85)
    ├─ Partial match   (0.50–0.85 → 0.60)
    └─ No match        → 0.0
    ↓
Blocklist Filter (remove false positives)
    ↓
Text Scan (surface form overrides for "communication" → "wrote", etc.)
    ↓
Weighted Score (tiered * importance multiplier)
```

### Final Score

```
Score = (Sum of matched skill weights) / (Total JD skills) * 100%
Capped at 100%
```

-----

## File Structure

```
ats_analyzer/
├── app.py                      # Streamlit UI, V1/V2/Compare modes
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── KNOWN_ISSUES.md
├── data/
│   └── feedback_log.json       # Thumbs up/down feedback
├── src/
│   ├── parser.py               # PDF/DOCX extraction, section detection
│   ├── skill_extractor.py      # Gemini API, fallback, caching
│   ├── semantic_matcher.py     # Sentence Transformer, scoring
│   ├── v1_matcher.py           # spaCy noun extraction (V1 only)
│   └── feedback.py             # Feedback logging
└── utils/
    └── helpers.py              # Formatting, score labels
```

-----

## Configuration

### Sidebar Settings

|Setting             |Default  |Purpose                                                  |
|--------------------|---------|---------------------------------------------------------|
|API Key             |—        |Gemini API key (optional; uses env var if set)           |
|Version             |V2       |V1 (spaCy), V2 (Gemini), or Compare                      |
|Similarity Threshold|0.55     |Min cosine similarity for partial match                  |
|Important Skills    |Unchecked|If checked, manually enter critical skills for 1.5x boost|
|Debug Mode          |Unchecked|Show raw extractions and section parsing                 |

### Scoring Ranges

|Score  |Decision                           |
|-------|-----------------------------------|
|80–100%|✅ Strong Match — likely to pass ATS|
|65–79% |⚠️ Good Match — may pass ATS        |
|50–64% |⚠️ Weak Match — may be filtered     |
|<50%   |❌ Poor Match — likely rejected     |

-----

## Known Issues & Status

### 🔴 Critical (Fixes in Progress)

|#|Issue                                                                  |Impact               |Status                                                            |
|-|-----------------------------------------------------------------------|---------------------|------------------------------------------------------------------|
|1|Gemini extraction inconsistency — same resume extracts 22 vs 26 skills |±5% score variance   |Fix: Use `st.session_state` cache instead of module dict          |

### 🟡 Medium Priority (V2.2 Roadmap)

|#|Issue                                 |Effort|Workaround                               |
|-|--------------------------------------|------|-----------------------------------------|
|4|ALL CAPS section headers not detected |Low   |Manually adjust resume formatting        |
|5|Soft skills need broader surface forms|Low   |Extend `SURFACE_FORM_OVERRIDES` dict     |
|6|Gemini prompt could be more exhaustive|Medium|Refine extraction rules in `build_prompt`|

### 🟢 Future (V3+)

- Seniority detection (“5+ years Python” vs “1 year Python”)
- Section weighting (skills 1.0x, experience 0.9x, summary 0.8x)
- Auto-detect critical skills from JD (“required”, “must have” keywords)
- Temperature scheduling for more consistent Gemini output
- Substring matching fixes for spaCy fallback (`\b` word boundaries)

-----

## Accuracy Benchmarks

Tested against known resume/JD pairs:

|Resume                     |JD                      |Expected|Current|Notes                                       |
|---------------------------|------------------------|--------|-------|--------------------------------------------|
|Data Analyst               |Data Analyst            |65–80%  |~42–44%|Missing Power BI; awaiting session cache fix|
|Cybersecurity (Alex Turner)|Senior Security Engineer|52–58%  |~42–44%|Missing pentest, cloud, offensive tools     |
|Cybersecurity              |Data Analyst            |<25%    |~20%   |✅ Domain confusion correctly low            |


> Expected accuracy post-fix: **+8–12%** (52–56% on security role).

-----

## Recent Changes (v2.1)

### Fixed

- ✅ Score capping at 100% (min/max bug)
- ✅ Multi-word skill extraction whitespace handling
- ✅ Division by zero when JD has no skills
- ✅ Gemini JSON parsing hardened (regex + `re.DOTALL` for markdown fence stripping)
- ✅ JD skill normalisation (certifications, tool variants)

### Added

- ✅ Session state caching (partial — module-level dict still used, needs replacement)
- ✅ Text scan surface form overrides (dynamic fallback to skill name)
- ✅ Per-skill thresholds (soft 0.50, hard 0.55)
- ✅ Feedback logging to JSON
- ✅ Debug mode with extraction inspection

-----

## Usage Examples

### Basic Usage

1. Upload resume (PDF/DOCX)
1. Paste job description
1. Click **“Analyse”**
1. View score, matched skills, missing skills, recommendations

### Advanced: Important Skills

1. Enable **“Mark important skills”** toggle
1. Enter critical skills (comma-separated): `python, aws, machine learning`
1. Re-analyse — these skills now weighted 1.5x
1. Score reflects criticality

### Debug Mode

1. Enable **“Debug mode”** toggle
1. View:
- Raw text extraction
- Section detection
- Gemini extraction (JSON)
- Matched vs missing skills with similarity scores
- Fallback explanation (if spaCy used)

-----
## Limitations

> ⚠️ Not production-grade for high-stakes hiring — use as a screening tool only.

- LLM extraction is ~90% accurate; some implicit skills may be missed
- Semantic matching requires both resume and JD to mention skills explicitly
- Blocklist is manually curated; new false positives may emerge
- ESCO taxonomy integration removed in V2 (was too rigid; Gemini extraction is more flexible)
- No seniority detection (“1 year” vs “5+ years” treated equally)

-----



## Acknowledgements

- [Gemini API](https://aistudio.google.com/) for LLM extraction
- [Sentence Transformers](https://huggingface.co/sentence-transformers) (HuggingFace) for semantic matching
- [spaCy](https://spacy.io/) for NLP fallback
- [Streamlit](https://streamlit.io/) for rapid UI prototyping
-----
