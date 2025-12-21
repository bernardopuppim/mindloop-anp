# backend/services/lats_service.py

from typing import Dict, Any
import logging

from lats_sistema.graph.build import build_graph
from backend.models import PredictRequest, HitlContinueRequest, PredictResponse
from lats_sistema.utils.confidence import traduzir_confianca
from lats_sistema.utils.output_formatter import formatar_saida_final

logger = logging.getLogger(__name__)

# Lazy loading do grafo para compatibilidade com Vercel (cold start)
_graph_cache = None

def get_graph():
    """Retorna grafo LATS (lazy loaded e cacheado)"""
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = build_graph()
        logger.info("✓ Grafo LATS compilado")
    return _graph_cache

# ============================================================================
# EXECUÇÃO NORMAL - RAG + LATS com HITL durante execução
# ============================================================================

def executar_primeira_fase(req: PredictRequest) -> PredictResponse:
    """
    Executa o grafo completo (RAG + LATS).

    ⚡ OTIMIZAÇÃO: Por padrão, RAG é DESABILITADO (SKIP_RAG_DEFAULT=1).
    Isto economiza ~2-5s e reduz custo em ~40%.

    Se durante a execução do LATS a entropia for alta:
      - HITL é acionado automaticamente
      - Grafo retorna com hitl_required=True
      - State contém checkpoint completo (ultimo_node, etc)

    Args:
        req: PredictRequest com texto_evento

    Returns:
        PredictResponse:
        - hitl_required=True → LATS pausou, aguardando decisão
        - hitl_required=False → Classificação concluída
    """
    from lats_sistema.config.fast_mode import SKIP_RAG_DEFAULT

    # Estado inicial
    state = req.state or {}
    state["descricao_evento"] = req.texto_evento

    # ⚡ OTIMIZAÇÃO: Controlar se RAG deve executar
    # Por padrão, RAG é PULADO (economiza tempo e tokens)
    if "_skip_rag" not in state:
        state["_skip_rag"] = SKIP_RAG_DEFAULT

    if req.contexto_normativo:
        state["contexto_normativo"] = req.contexto_normativo
        # Se contexto já foi fornecido, não precisa RAG
        state["_skip_rag"] = True

    # Executar grafo completo (RAG → LATS)
    # Se HITL for necessário, o engine LATS detecta e salva checkpoint
    result = get_graph().invoke(state)

    # Traduzir log_prob em confiança (se houver resultado final)
    confianca = None
    resultado_formatado = None

    if result.get("final"):
        log_prob = result["final"].get("log_prob")
        if log_prob is not None:
            confianca = traduzir_confianca(log_prob)

        # ✨ Formatar saída para apresentação profissional
        resultado_formatado = formatar_saida_final(
            resultado_final=result["final"],
            descricao_evento=req.texto_evento
        )

    return PredictResponse(
        hitl_required=result.get("hitl_required", False),
        hitl_metadata=result.get("hitl_metadata"),
        final=result.get("final"),
        confianca=confianca,  # Mantido para compatibilidade
        resultado_formatado=resultado_formatado,  # ✨ NOVO
        state=result
    )


# ============================================================================
# CONTINUAÇÃO APÓS HITL
# ============================================================================
def continuar_pos_hitl(req: HitlContinueRequest) -> PredictResponse:
    """
    Retoma LATS após decisão humana.

    O state deve conter o checkpoint salvo pelo LATS:
      - ultimo_node
      - ultimo_avaliacoes
      - ultimo_probs
      - etc

    Args:
        req: HitlContinueRequest com state e selected_child

    Returns:
        PredictResponse
    """
    state = req.state
    state["hitl_selected_child"] = req.selected_child

    # ===================================================================
    # FALLBACK DE JUSTIFICATIVA
    # ===================================================================
    # Se usuário não forneceu justificativa, usar a do modelo
    justificativa_final = req.justification

    if not justificativa_final or justificativa_final.strip() == "":
        # Buscar justificativa do modelo para o filho escolhido
        ultimo_avaliacoes = state.get("ultimo_avaliacoes", [])
        for aval in ultimo_avaliacoes:
            if aval.get("id") == req.selected_child:
                justificativa_final = aval.get("justificativa", "")
                break

        # Se ainda não encontrou, usar fallback genérico
        if not justificativa_final:
            justificativa_final = f"Decisão selecionada: {req.selected_child}"

    state["hitl_justification"] = justificativa_final

    logger.info("="*80)
    logger.info(" 🔄 CONTINUANDO APÓS DECISÃO HUMANA")
    logger.info("="*80)
    logger.info(f"➡️  Escolha do usuário: {req.selected_child}")
    if req.justification and req.justification.strip():
        logger.info(f"➡️  Justificativa (humana): {justificativa_final}")
    else:
        logger.info(f"➡️  Justificativa (modelo): {justificativa_final}")
    logger.info("="*80)

    # Executar/retomar grafo
    # O engine LATS detecta hitl_selected_child e chama _continuar_pos_hitl
    result = get_graph().invoke(state)

    # Traduzir log_prob em confiança (se houver resultado final)
    confianca = None
    resultado_formatado = None

    if result.get("final"):
        log_prob = result["final"].get("log_prob")
        if log_prob is not None:
            confianca = traduzir_confianca(log_prob)

        # ✨ Formatar saída para apresentação profissional
        # Recuperar evento original do state
        descricao_evento = state.get("descricao_evento", "Evento não especificado")
        resultado_formatado = formatar_saida_final(
            resultado_final=result["final"],
            descricao_evento=descricao_evento
        )

    return PredictResponse(
        hitl_required=result.get("hitl_required", False),
        hitl_metadata=result.get("hitl_metadata"),
        final=result.get("final"),
        confianca=confianca,  # Mantido para compatibilidade
        resultado_formatado=resultado_formatado,  # ✨ NOVO
        state=result
    )
