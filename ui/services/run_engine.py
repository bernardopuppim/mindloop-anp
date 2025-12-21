# ui/services/run_engine.py

from typing import Dict, Any, Optional

from lats_sistema.graph.nodes import no_rag
from lats_sistema.lats.engine import executar_lats


# ================================================================
# 1) Primeira fase — roda RAG + LATS até parar em:
#    - final
#    - ou HITL intermediário
#    - ou HITL FINAL
# ================================================================
def executar_primeira_fase(descricao_evento: str) -> Dict[str, Any]:
    """
    Primeira chamada: roda RAG + LATS até:
      - encontrar um resultado final, ou
      - acionar HITL intermediário, ou
      - acionar HITL FINAL
    """

    state: Dict[str, Any] = {
        "descricao_evento": descricao_evento,
    }

    # 1) Contextualização RAG
    state = no_rag(state)

    # 2) Execução do LATS-P (pode parar em HITL)
    state = executar_lats(state)

    return state


# ================================================================
# 2) Continuação após HITL intermediário OU HITL FINAL
#    Ambos tratados aqui com parâmetros opcionais
# ================================================================
def executar_pos_hitl(
    state: Dict[str, Any],
    child_id: Optional[str] = None,
    justificativa: Optional[str] = None,
    final_correto: Optional[bool] = None,
    classe_corrigida: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executa a continuação após intervenção humana (HITL).

    Existem DOIS TIPOS de HITL:

    🔹 1) HITL intermediário
        - child_id != None
        - lógica normal do LATS continua a partir do nó escolhido

    🔹 2) HITL final
        - child_id = None
        - final_correto = True  → humano aceitou
        - final_correto = False → humano corrigiu e forneceu classe_corrigida
    """

    # ---------------------------------------------------------
    # Caso 1 — HITL intermediário
    # ---------------------------------------------------------
    if child_id is not None:
        state["hitl_selected_child"] = child_id
        state["hitl_justification"] = justificativa or None

        # Executa continuação normal
        return executar_lats(state)

    # ---------------------------------------------------------
    # Caso 2 — HITL FINAL
    # ---------------------------------------------------------
    state["hitl_final_required"] = False  # final já resolvido

    if final_correto is True:
        # Usuário aceitou o resultado do modelo
        state["validacao_final"] = {
            "status": "aceito",
            "justificativa": justificativa or None,
            "classe_final_modelo": state.get("final", {}).get("node_id"),
        }
        return state

    if final_correto is False:
        # Usuário corrigiu o resultado final
        state["validacao_final"] = {
            "status": "corrigido",
            "classe_final_modelo": state.get("final", {}).get("node_id"),
            "classe_corrigida_humano": classe_corrigida,
            "justificativa": justificativa or None,
        }
        return state

    # Se chegar aqui, algo está inconsistente
    raise RuntimeError("executar_pos_hitl chamado sem parâmetros suficientes.")
