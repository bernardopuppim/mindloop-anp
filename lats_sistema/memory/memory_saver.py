# ================================================================
# memory_saver.py — lógica de salvamento inteligente de memória HITL
# ================================================================

from lats_sistema.memory.db import insert_decision
from lats_sistema.memory.faiss_store import add_vector, search_vectors
from lats_sistema.models.embeddings import embeddings
import numpy as np

ENTROPY_THRESHOLD = 1.0
DUPLICATE_DISTANCE_THRESHOLD = 0.15   # quanto menor, mais parecido
TOP_K_DUP_CHECK = 5


def modelo_top_choice(tracking_children):
    """Retorna o filho mais provável segundo o modelo."""
    if not tracking_children:
        return None
    sorted_children = sorted(tracking_children, key=lambda x: x["prob"], reverse=True)
    return sorted_children[0]["id"]


def deve_salvar_memoria(node_id, chosen_child, tracking_children, entropia_local):
    """
    Decide SE vale a pena salvar a justificativa humana.
    """

    modelo_top = modelo_top_choice(tracking_children)

    # 1) Caso humano corrige o modelo → sempre salvar
    if modelo_top != chosen_child:
        return True, "correcao_modelo"

    # 2) Caso modelo está incerto → salvar para fortalecer
    if entropia_local >= ENTROPY_THRESHOLD:
        return True, "alta_entropia"

    # Caso contrário, não salvar
    return False, "modelo_confiante"


def memoria_muito_parecida(embed_vec: np.ndarray, node_id: str) -> bool:
    """
    Checa duplicação REAL usando FAISS (distância vetorial).
    """

    try:
        ids, dist = search_vectors(embed_vec, TOP_K_DUP_CHECK)
    except Exception:
        return False

    for d, distance in zip(ids, dist):
        if d < 0:
            continue

        # Quanto menor distância, mais parecido
        if distance <= DUPLICATE_DISTANCE_THRESHOLD:
            return True

    return False


def salvar_memoria_if_applicable(
    state,
    node_id,
    chosen_child,
    justificativa_humana,
    justificativa_modelo,
    entropia_local,
    avaliacoes,
    probs
):
    """
    Verifica regras e salva memória (SQLite + FAISS)
    somente quando fizer sentido.
    """

    descricao_evento = state.get("descricao_evento", "")
    tracking_children = state.get("ultimo_tracking_children", [])

    # -----------------------------
    # ETAPA 1 — verificar SE deve salvar
    # -----------------------------
    salvar, motivo = deve_salvar_memoria(
        node_id=node_id,
        chosen_child=chosen_child,
        tracking_children=tracking_children,
        entropia_local=entropia_local
    )

    if not salvar:
        print(f"💾 [MEMÓRIA] Não será salva — motivo: {motivo}")
        return

    # -----------------------------
    # ETAPA 2 — gerar embedding
    # -----------------------------
    embed_vec = embeddings.embed_query(descricao_evento)
    embed_vec = np.array(embed_vec, dtype="float32")

    # -----------------------------
    # ETAPA 3 — evitar duplicadas via embeddings
    # -----------------------------
    if memoria_muito_parecida(embed_vec, node_id):
        print("💾 [MEMÓRIA] Pulando — memória muito semelhante já registrada.")
        return

    # -----------------------------
    # ETAPA 4 — extrair sugestão do modelo
    # -----------------------------
    filhos_ordenados = sorted(
        [{"id": a["id"], "score": a["score"], "prob": float(p), "justificativa": a.get("justificativa", "")}
         for a, p in zip(avaliacoes, probs)],
        key=lambda x: x["prob"],
        reverse=True
    )

    modelo_suggestion = filhos_ordenados[0]["id"]
    modelo_just = filhos_ordenados[0]["justificativa"]

    # -----------------------------
    # ETAPA 5 — salvar no SQLite
    # -----------------------------
    data = {
        "event_text": descricao_evento,
        "node_id": node_id,
        "chosen_child": chosen_child,
        "model_suggestion": modelo_suggestion,
        "justification_human": justificativa_humana,
        "justification_model": modelo_just,
        "entropy": entropia_local,
        "embedding": embed_vec.tobytes(),
    }

    mem_id = insert_decision(data)

    # -----------------------------
    # ETAPA 6 — salvar FAISS
    # -----------------------------
    add_vector(embed_vec, mem_id)

    print(f"💾 [MEMÓRIA] Registrada com id={mem_id} (motivo: {motivo})")
