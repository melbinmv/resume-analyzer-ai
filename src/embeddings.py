from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def similarity(text1, text2):

    emb1 = model.encode([text1])
    emb2 = model.encode([text2])

    score = cosine_similarity(emb1, emb2)[0][0]

    return score