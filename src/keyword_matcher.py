import spacy

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text)

    keywords = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            keywords.append(token.text.lower())

    return list(set(keywords))

def match_keywords(resume_keywords, job_keywords):

    matched = set(resume_keywords).intersection(set(job_keywords))

    return {
        "matched": list(matched),
        "missing": list(set(job_keywords) - set(resume_keywords))
    }