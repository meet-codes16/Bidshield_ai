from typing import Sequence
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RAGService:
    """Local deterministic fallback. In production, replace the vector repository with pgvector/Qdrant."""
    def retrieve(self, query: str, chunks: Sequence[dict], top_k=5):
        if not chunks: return []
        texts=[c["text"] for c in chunks]
        try:
            X=TfidfVectorizer(stop_words="english").fit_transform([query]+texts)
            scores=cosine_similarity(X[0:1],X[1:]).ravel()
        except ValueError:
            scores=[0.0]*len(texts)
        ids=sorted(range(len(texts)),key=lambda i:scores[i],reverse=True)[:top_k]
        return [{**chunks[i],"score":round(float(scores[i]),4)} for i in ids]
