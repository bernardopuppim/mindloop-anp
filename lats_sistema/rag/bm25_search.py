from rank_bm25 import BM25Okapi

def buscar_bm25(query, corpus, n=5):
    tokens = [c.split() for c in corpus]
    bm25 = BM25Okapi(tokens)
    scores = bm25.get_scores(query.split())
    idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
    return [corpus[i] for i in idx]
