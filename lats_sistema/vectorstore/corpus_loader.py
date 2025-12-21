import os, re, tiktoken
from typing import List
from lats_sistema.vectorstore.faiss_loader import faiss_store

encoding = tiktoken.get_encoding("o200k_base")

def chunk_md(texto: str, max_tokens=500, overlap=100):
    tokens = encoding.encode(texto)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk = encoding.decode(tokens[start:end])
        chunks.append(chunk)
        start += max_tokens - overlap
    return chunks

def carregar_corpus_normativo(dir_path="padroes_petrobras") -> List[str]:
    corpus = []

    for fn in os.listdir(dir_path):
        if fn.endswith(".md"):
            text = open(os.path.join(dir_path, fn), encoding="utf-8").read()
            chunks = chunk_md(text)
            corpus.extend(chunks)

    try:
        docs = faiss_store.similarity_search("SMS", k=2000)
        corpus.extend([d.page_content for d in docs])
    except:
        pass

    return list(set(corpus))
