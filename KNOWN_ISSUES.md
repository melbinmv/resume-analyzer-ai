# Known Issues — Version 3 Roadmap

## Critical 🔴

### Issue 1 — Substring Matching
- **Problem:** "ski" matches inside "skills", "r" matches inside "requirements"
- **Impact:** Inflated scores from false matches
- **Fix:** Whole word boundary regex matching (\b)

### Issue 2 — ESCO Not Recognising Common Skills
- **Problem:** "python", "excel", "data analysis" not found in ESCO
- **Cause:** ESCO stores them as "use python programming language"
- **Impact:** ESCO validation is almost always empty
- **Fix:** Build label mapping or use fuzzy ESCO matching

### Issue 3 — spaCy Extracting Noise
- **Problem:** Extracts personal info, company names, phone numbers
- **Impact:** Noise pollutes resume skills and inflates score
- **Fix:** Section-aware parsing before extraction

---

## Medium 🟠

### Issue 4 — JD Extraction Too Loose
- **Problem:** Extracts sentence fragments not skills
- **Fix:** Line/comma split with ESCO validation

### Issue 5 — Score Inflated By Noise Matches
- **Problem:** Noise phrases accidentally match JD skills at low similarity
- **Fix:** Clean skills before matching, raise partial threshold

### Issue 6 — Important Skills Hardcoded
- **Problem:** User must manually enter important skills
- **Fix:** Auto-detect from JD using frequency and emphasis keywords
  ("must have", "required", "essential" = critical)
  ("preferred", "nice to have" = low priority)

---

## Low 🟡

### Issue 7 — No Section Weighting
- **Problem:** Skills section and experience section treated equally
- **Fix:** Weight by section (skills=1.0, experience=0.9, summary=0.8)

### Issue 8 — No Seniority Detection
- **Problem:** "5+ years Python" and "1 year Python" treated the same
- **Fix:** Extract and compare experience duration

### Issue 9 — PDF Formatting Loss
- **Problem:** Complex PDFs can break multi-word skills
- **Fix:** pdfminer fallback + DOCX support

### Issue 10 — No Feedback Loop
- **Problem:** System cannot learn from wrong scores
- **Fix:** Thumbs up/down feedback logged to database

---

## Version 3 Priority Order
| Priority | Issue                    | Effort | Impact |
|----------|--------------------------|--------|--------|
| 1        | ESCO label mismatch      | Medium | High   |
| 2        | Section-aware parsing    | Medium | High   |
| 3        | Word boundary matching   | Low    | High   |
| 4        | JD extraction cleanup    | Medium | Medium |
| 5        | Auto important skills    | Medium | Medium |
| 6        | Noise filtering          | Low    | Medium |
| 7        | Section weights          | Medium | Low    |
| 8        | Seniority detection      | High   | Low    |
| 9        | DOCX support             | Low    | Low    |
| 10       | Feedback loop            | High   | Low    |