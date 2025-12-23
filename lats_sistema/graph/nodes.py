# ================================================================
# graph/nodes.py — RAG + LATS-P + HITL (Streamlit + Prints)
# ================================================================

from typing import Dict, Any, List
from langchain_core.documents import Document
import logging

# ===================================================================
# LAZY IMPORTS CONDICIONAIS - Evita carregar FAISS em SERVERLESS MODE
# ===================================================================
from lats_sistema.config.fast_mode import SERVERLESS_FAST_MODE

# Imports sempre necessários (não dependem de FAISS)
from lats_sistema.lats.engine import executar_lats
from lats_sistema.lats.tree_loader import NODE_INDEX

logger = logging.getLogger(__name__)

# Imports pesados (RAG/FAISS) - apenas quando NÃO estiver em serverless mode
if not SERVERLESS_FAST_MODE:
    from lats_sistema.rag.hyde import hyde_generate
    from lats_sistema.rag.bm25_search import buscar_bm25
    from lats_sistema.rag.semantic_search import buscar_semantico
    from lats_sistema.rag.reranker import rerank
    from lats_sistema.rag.synthesizer import sintetizar
    from lats_sistema.vectorstore.corpus_loader import carregar_corpus_normativo
else:
    # Placeholders para evitar erros de nome não definido
    # Estes nunca serão chamados porque o RAG será bypassado
    hyde_generate = None
    buscar_bm25 = None
    buscar_semantico = None
    rerank = None
    sintetizar = None
    carregar_corpus_normativo = None
    logger.info("[SERVERLESS MODE] RAG imports bypassados - FAISS não será carregado")


# ================================================================
# Função de deduplicação de textos (strings e Documents)
# ================================================================
def deduplicar_textos(items: List) -> List[str]:
    """
    Remove textos duplicados de uma lista mista de strings e Documents.
    Preserva ordem do primeiro item encontrado.

    Args:
        items: Lista de strings ou Documents LangChain

    Returns:
        Lista deduplic ada de strings
    """
    vistos = set()
    resultado = []
    for item in items:
        # Normalizar para string
        if isinstance(item, str):
            texto = item.strip()
        elif hasattr(item, 'page_content'):
            texto = item.page_content.strip()
        else:
            texto = str(item).strip()

        # Deduplicar
        if texto and texto not in vistos:
            vistos.add(texto)
            resultado.append(texto)

    return resultado


# ================================================================
# Nó RAG — com prints e FAST_MODE support
# ================================================================
def no_rag(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nó RAG com controle de execução condicional.

    ⚡ OTIMIZAÇÃO: RAG só executa se explicitamente solicitado via state.
    Permite que LATS-P inicie sem RAG e só execute quando necessário.

    🚀 SERVERLESS MODE: RAG é completamente bypassado quando SERVERLESS_FAST_MODE=true
    """
    from lats_sistema.config.fast_mode import (
        SERVERLESS_FAST_MODE,
        FAST_MODE_ENABLED,
        RAG_HYDE_ENABLED,
        RAG_BM25_K,
        RAG_SEMANTIC_K,
        RAG_RERANK_TOP_N,
        RAG_MAX_CONTEXT_LENGTH,
    )

    # 🚀 BYPASS AUTOMÁTICO: Modo serverless sempre pula RAG
    if SERVERLESS_FAST_MODE:
        logger.info("="*70)
        logger.info("[RAG BYPASS] Execução pulada (SERVERLESS_FAST_MODE ativo)")
        logger.info("[RAG BYPASS] Pipeline RAG desabilitado - FAISS não carregado")
        logger.info("="*70)
        state["contexto_normativo"] = ""
        return state

    # ⚡ BYPASS: Se RAG foi explicitamente desabilitado, pular execução
    if state.get("_skip_rag", False):
        logger.info("\n⚡ RAG BYPASS: Execução pulada (contexto não necessário)")
        state["contexto_normativo"] = ""
        return state

    evento = state["descricao_evento"]

    print("\n==============================")
    if FAST_MODE_ENABLED:
        print(" ⚡ RAG: Gerando contexto (FAST MODE)")
    else:
        print(" 📘 RAG: Gerando contexto")
    print("==============================\n")
    print(f"Evento: {evento}\n")

    # HyDE (condicional)
    if RAG_HYDE_ENABLED:
        hyde_doc = hyde_generate(evento)
        query_rag = evento + " " + hyde_doc
        print("✓ HyDE gerado")
    else:
        hyde_doc = ""
        query_rag = evento
        print("⚡ HyDE desabilitado (FAST_MODE)")

    # BM25 + Semântico com k configurável
    corpus = carregar_corpus_normativo()
    bm25 = buscar_bm25(query_rag, corpus, n=RAG_BM25_K)  # usa parâmetro 'n'
    sem_all = buscar_semantico(evento)  # retorna todos
    sem = sem_all[:RAG_SEMANTIC_K]  # limita manualmente

    print(f"✓ BM25: {len(bm25)} docs | Semântico: {len(sem)} docs")

    # Combinar candidatos e deduplicar (normaliza tudo para strings)
    candidatos = deduplicar_textos(bm25 + sem)
    if hyde_doc:
        candidatos.append(hyde_doc)

    # Rerank - pega todos e limita depois
    ranking_all = rerank(evento, candidatos)
    ranking = ranking_all[:RAG_RERANK_TOP_N]

    # Sintetizar
    contexto = sintetizar(evento, ranking)

    # Limitar tamanho do contexto se necessário
    if len(contexto) > RAG_MAX_CONTEXT_LENGTH:
        contexto = contexto[:RAG_MAX_CONTEXT_LENGTH] + "... [truncado]"

    print(f"✓ Contexto final: {len(contexto)} caracteres\n")

    state["contexto_normativo"] = contexto
    return state


# ================================================================
# Nó de classificação — com print
# ================================================================
def no_classificar(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n==============================")
    print(" 🤖 CLASSIFICADOR: executando LATS-P")
    print("==============================\n")
    return executar_lats(state)


# ================================================================
# Nó HITL — prints, sem input(), sem Interrupt
# ================================================================

# ❌ REMOVIDO: O Interrupt NÃO deve ser importado,
# pois causa GraphRecursionError no fluxo Streamlit
# from langgraph.graph import Interrupt


def no_hitl(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    ✅ CORREÇÃO HITL - Este nó FINALIZA o grafo (retorna para frontend).

    O grafo agora faz: classificar → hitl → END
    O frontend deve chamar /hitl/continue para retomar a execução.
    """
    meta = state.get("hitl_metadata", {}) or {}
    node_id = meta.get("node_id", "N/D")

    print("\n" + "="*60)
    print(" 🔥 HITL ACIONADO - EXECUÇÃO PAUSADA")
    print("="*60 + "\n")

    print(f"📍 Nó atual       : {node_id}")
    print(f"❓ Pergunta       : {meta.get('pergunta')}")
    print(f"📊 Profundidade   : {meta.get('depth')}")
    print(f"🌀 Entropia local : {meta.get('entropia_local'):.3f}\n")

    print("👥 Filhos disponíveis:")
    children = meta.get("children", [])
    for i, c in enumerate(children):
        filho_node = NODE_INDEX.get(c["id"], {})
        print(f"\n [{i}] ID: {c['id']}")
        print(f"     Score: {c['score']:.3f} | Prob: {c['prob']:.3f}")
        print(f"     Texto: {filho_node.get('pergunta','(sem texto)')}")
        print(f"     Justificativa: {c.get('justificativa','')}")

    print("\n" + "="*60)
    print(" ⏸️  AGUARDANDO RESPOSTA HUMANA")
    print(" ℹ️  O grafo foi FINALIZADO e retornou para o frontend.")
    print(" ℹ️  Use /hitl/continue para retomar após escolha.")
    print("="*60 + "\n")

    state.setdefault("logs", []).append(
        f"HITL acionado no nó {node_id} - execução pausada, aguardando input humano"
    )

    # ✅ CORREÇÃO: Retorna state normalmente
    # O grafo agora tem edge hitl → END, então a execução PARA aqui
    # O backend retornará hitl_required=True para o frontend
    return state


# ================================================================
# HITL FINAL — prints sem input()
# ================================================================
def no_hitl_final(state: Dict[str, Any]) -> Dict[str, Any]:
    final = state.get("final")

    print("\n==============================")
    print(" 📝 VALIDAÇÃO FINAL (HITL FINAL)")
    print("==============================\n")

    if not final:
        print("❗ Nenhum resultado final disponível.\n")
        state["validacao_final"] = {"status": "sem_final"}
        return state

    node_id = final["node_id"]
    classe_final = NODE_INDEX[node_id].get("classe", "Classe_indefinida")

    print(f"📌 Classe sugerida : {classe_final}")
    print(f"📍 Nó final        : {node_id}\n")
    print("➡️ Aguardando validação humana na interface Streamlit...\n")

    state.setdefault("logs", []).append(
        f"Validação final necessária — classe sugerida: {classe_final}"
    )

    return state
