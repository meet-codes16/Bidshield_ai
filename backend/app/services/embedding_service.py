import hashlib, math
class LocalEmbeddingProvider:
    """Small deterministic embedding for offline demos; use a real embedding model in production."""
    def embed(self,text):
        v=[0.0]*384
        for token in text.lower().split():
            i=int(hashlib.sha256(token.encode()).hexdigest(),16)%384
            v[i]+=1.0
        n=math.sqrt(sum(x*x for x in v)) or 1
        return [x/n for x in v]
