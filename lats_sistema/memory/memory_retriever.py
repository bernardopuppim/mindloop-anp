# lats_sistema/memory/memory_retriever.py

from .db import get_decision_by_id
from .faiss_store import search_vectors
from lats_sistema.utils.embedding_cache import get_event_embedding
import numpy as np


def buscar_justificativas_semelhantes(descricao_evento: str, node_id: str, k: int = 3, state: dict = None):
    """
    Recupera memórias humanas relevantes para um nó da árvore.

    🔹 Gera embedding do evento
    🔹 Busca vetores similares no FAISS
    🔹 Filtra apenas memórias referentes ao node_id
    🔹 Retorna lista com:
        {
           "event_text": str,
           "chosen_child": str,
           "justification_human": str
        }
    """

    if not descricao_evento or not node_id:
        return []

    # 1) Gerar embedding do evento (usando cache se disponível)
    try:
        if state is not None:
            # ⚡ OTIMIZAÇÃO: Reutiliza embedding cached do state
            embed_vec = get_event_embedding(state, descricao_evento)
        else:
            # Fallback se state não foi passado (backward compatibility)
            from lats_sistema.models.embeddings import embeddings
            embed_vec = embeddings.embed_query(descricao_evento)
            embed_vec = np.array(embed_vec).astype("float32")
    except Exception as e:
        # Fallback silencioso - memória não é crítica
        return []

    # 2) Busca FAISS
    try:
        ids, _ = search_vectors(embed_vec, k)
    except Exception as e:
        # FAISS index não inicializado - normal em primeira execução
        # Sistema continua sem memória episódica (não é erro crítico)
        return []

    if ids is None:
        return []

    mems = []

    # 3) Recuperar do banco (somente memórias daquele node_id)
    for did in ids:
        if did < 0:
            continue

        row = get_decision_by_id(int(did))
        if not row:
            continue

        if row.get("node_id") != node_id:
            continue

        mems.append({
            "event_text": row.get("event_text", ""),
            "chosen_child": row.get("chosen_child", ""),
            "justification_human": row.get("justification_human", ""),
        })

    return mems
