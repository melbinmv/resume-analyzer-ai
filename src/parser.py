import pdfplumber
import re


def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(lines)


def extract_text_from_docx(file):
    try:
        from docx import Document as DocxDocument
        doc   = DocxDocument(file)
        lines = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(lines)
    except ImportError:
        print("⚠️  python-docx not installed. Run: pip install python-docx")
        return ""
    except Exception as e:
        print(f"⚠️  DOCX extraction error: {e}")
        return ""


def extract_text(file, file_type):
    file_type = file_type.lower().strip(".")
    if file_type == "pdf":
        return extract_text_from_pdf(file)
    elif file_type in ["docx", "doc"]:
        return extract_text_from_docx(file)
    else:
        print(f"⚠️  Unsupported file type: {file_type}")
        return ""


# ─────────────────────────────────────
# SECTION_HEADERS
# FIX: added certifications, awards, languages sections so
#      they are parsed and passed to Gemini for extraction.
#
# Design principle — kept comprehensive but generic:
#   Headers cover all common resume section naming conventions
#   across domains, cultures, and career levels.
# ─────────────────────────────────────
SECTION_HEADERS = {
    "summary": [
        "summary", "profile", "about me", "objective",
        "professional summary", "personal statement",
        "career objective", "career summary",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "key skills", "technologies", "tools",
        "technical competencies", "areas of expertise",
        "expertise", "competencies",
    ],
    "experience": [
        "experience", "work experience", "employment history",
        "professional experience", "work history",
        "career history", "employment", "positions held",
    ],
    "education": [
        "education", "academic background", "qualifications",
        "academic qualifications", "academic history",
        "educational background",
    ],
    "projects": [
        "projects", "personal projects", "key projects",
        "portfolio", "selected projects", "notable projects",
        "open source", "side projects",
    ],
    # ── FIX: certifications section added ─────────────────
    "certifications": [
        "certifications", "certification", "certificates",
        "professional certifications", "licences", "licenses",
        "accreditations", "credentials", "professional development",
        "courses", "training",
    ],
    # ── Additional common sections ─────────────────────────
    "awards": [
        "awards", "achievements", "honours", "honors",
        "recognition", "accomplishments",
    ],
    "languages": [
        "languages", "language skills",
    ],
    "publications": [
        "publications", "research", "papers",
    ],
    "volunteer": [
        "volunteer", "volunteering", "community",
        "extracurricular",
    ],
}


def detect_section(line):
    line_clean = line.strip().lower()
    line_clean = re.sub(r"^[\•\-\*\●\>\·]\s*", "", line_clean)

    # Handle ALL CAPS headers (common in PDFs)
    # e.g. "WORK EXPERIENCE" → "work experience"
    for section, headers in SECTION_HEADERS.items():
        if line_clean in headers:
            return section

    return None


def split_into_sections(text):
    sections = {}
    current  = "header"
    sections[current] = []

    for line in text.splitlines():
        detected = detect_section(line)
        if detected:
            current = detected
            sections[current] = []
        else:
            sections.setdefault(current, []).append(line)

    return {
        section: " ".join(lines).strip()
        for section, lines in sections.items()
        if any(l.strip() for l in lines)
    }


def extract_resume_sections(file, file_type="pdf"):
    raw_text = extract_text(file, file_type)

    if not raw_text:
        print("⚠️  No text extracted from file")
        return {"full_text": "", "sections": {}}

    sections = split_into_sections(raw_text)
    print(f"✅ Sections detected: {list(sections.keys())}")

    return {
        "full_text": raw_text,
        "sections" : sections
    }