# lats_sistema/memory/faiss_store.py

import faiss
import numpy as np
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parent / "faiss_index.bin"


# -----------------------------------------------------------
# Criar índice FAISS com suporte a IDs reais (SQLite IDs)
# -----------------------------------------------------------
def create_index(dim: int):
    """
    Cria um índice FAISS persistente com IDMap,
    permitindo que cada vetor tenha um ID customizado.
    """
    
    index_flat = faiss.IndexFlatL2(dim)   # base
    index = faiss.IndexIDMap(index_flat)  # agora suporta IDs reais

    faiss.write_index(index, str(INDEX_PATH))
    return index


# -----------------------------------------------------------
# Carregar índice existente
# -----------------------------------------------------------
def load_index():
    if not INDEX_PATH.exists():
        raise RuntimeError(
            f"FAISS index not found at {INDEX_PATH}. "
            "Run create_index(dim) before inserting vectors."
        )
    return faiss.read_index(str(INDEX_PATH))


# -----------------------------------------------------------
# Adicionar vetor com ID = decision_id (SQLite)
# -----------------------------------------------------------
def add_vector(vec: np.ndarray, decision_id: int):
    """
    Adiciona um vetor ao índice FAISS com ID correspondente ao ID do banco SQLite.
    """
    
    index = load_index()

    if vec.ndim == 1:
        vec = vec.reshape(1, -1)

    vec = vec.astype("float32")

    ids = np.array([decision_id], dtype=np.int64)

    index.add_with_ids(vec, ids)
    faiss.write_index(index, str(INDEX_PATH))


# -----------------------------------------------------------
# Busca vetores similares (retorna ids e distâncias)
# -----------------------------------------------------------
def search_vectors(vec: np.ndarray, k=3):
    """
    Busca vetores mais similares no FAISS.
    Retorna:
        ids (list)
        distances (list)
    """

    index = load_index()

    if index.ntotal == 0:
        # FAISS vazio → nada para retornar
        return [], []

    if vec.ndim == 1:
        vec = vec.reshape(1, -1)

    vec = vec.astype("float32")

    distances, ids = index.search(vec, k)

    return ids[0], distances[0]
