# lats_sistema/utils/embedding_cache.py
"""
Cache global de embeddings do evento para evitar recálculo.

OTIMIZAÇÃO: O embedding do evento é imutável durante todo o LATS-P.
Calcular uma vez e reutilizar economiza ~50-80% das chamadas à API de embeddings.
"""

from typing import Optional
import numpy as np
from lats_sistema.models.embeddings import embeddings


def get_event_embedding(state: dict, evento_texto: str) -> np.ndarray:
    """
    Obtém embedding do evento, usando cache do state se disponível.

    Args:
        state: State do LangGraph (onde o cache é armazenado)
        evento_texto: Texto do evento

    Returns:
        np.ndarray: Embedding vetorial do evento
    """
    # Verificar se já existe no cache
    cached_embedding = state.get("_event_embedding_cache")

    if cached_embedding is not None:
        # Cache hit - não fazer nova chamada à API
        return np.array(cached_embedding).astype("float32")

    # Cache miss - calcular embedding
    print("🔵 Gerando embedding do evento (primeira vez)")
    embed_vec = embeddings.embed_query(evento_texto)
    embed_vec = np.array(embed_vec).astype("float32")

    # Salvar no state para reutilização
    state["_event_embedding_cache"] = embed_vec.tolist()

    return embed_vec


def clear_event_embedding_cache(state: dict):
    """
    Limpa cache de embedding (útil para testes).

    Args:
        state: State do LangGraph
    """
    if "_event_embedding_cache" in state:
        del state["_event_embedding_cache"]
        print("🗑️ Cache de embedding limpo")
