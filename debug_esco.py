# Run this as a standalone script
# save as debug_esco.py and run: python debug_esco.py

import pandas as pd

df = pd.read_csv("data/skills_en.csv")

search_terms = [
    "python", "excel", "sql",
    "data analysis", "data visualization",
    "power bi", "machine learning"
]

for term in search_terms:
    matches = df[
        df["preferredLabel"].str.contains(term, case=False, na=False)
    ]["preferredLabel"].tolist()

    print(f"\n'{term}' in ESCO:")
    print(matches[:5])  # show first 5 matches