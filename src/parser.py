# =========================
# 📁 src/parser.py
# =========================

import pdfplumber

def extract_text_from_pdf(file):
    """
    Extracts and cleans text from a PDF file.
    Handles newlines and whitespace issues from pdfplumber.
    """
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Normalize whitespace
    # Fixes issues like "Data\nAnalysis" → "Data Analysis"
    text = " ".join(text.split())

    return text