# Changelog

All notable changes to this project are documented here.

---

## [Version 2.0] — Current

### Added
- Semantic matching using Sentence Transformers (all-MiniLM-L6-v2)
- ESCO skills taxonomy integration (13,000+ skills)
- spaCy noun chunk extraction for implied skills
- Weighted scoring tiers (exact / strong / partial / none)
- Important skills multiplier (1.5x boost)
- Score capped at 100% (min/max fix)
- Streamlit UI with sidebar settings
- Adjustable similarity threshold slider
- Debug mode with raw text and skill inspection
- Matched vs missing skills display
- Recommendations section with priority levels

### Changed
- Scoring formula now uses weighted tiers not binary match
- Skill extraction now uses ESCO + spaCy not fixed list
- app.py restructured with columns and expanders

### Fixed
- Score exceeding 100% bug
- Multi-word skill extraction whitespace bug
- Division by zero when JD has no skills

---

## [Version 1.0]

### Added
- Basic keyword matching (rule-based)
- Fixed KNOWN_SKILLS list
- Simple ATS score: matched/total * 100
- PDF text extraction using pdfplumber
- Basic Streamlit UI

---

## Known Issues → See KNOWN_ISSUES.md