# lats_sistema/config/fast_mode.py
"""
FAST_MODE - Otimizações de performance SEM quebrar HITL.

PERMITIDO:
- Desabilitar HyDE
- Reduzir k do RAG (contexto menor)
- Cachear embeddings
- Limitar max_tokens

PROIBIDO:
- Pular HITL
- Reduzir thresholds de entropia
- Escolher automaticamente nós
"""

import os
from typing import Dict, Any


# ===================================================================
# CONFIGURAÇÃO FAST_MODE
# ===================================================================
FAST_MODE_ENABLED = os.getenv("FAST_MODE", "0") == "1"


# ===================================================================
# CONFIGURAÇÃO SERVERLESS_FAST_MODE
# ===================================================================
# Modo serverless SEM RAG/FAISS para deploy em Vercel (limite 250 MB)
# Quando ativo:
# - ❌ NÃO importa FAISS
# - ❌ NÃO importa lats_sistema.rag.*
# - ❌ NÃO carrega embeddings
# - ✅ Mantém 100% da lógica LATS-P (heurísticas, poda, entropia, HITL)
# - ✅ RAG é automaticamente bypassado no grafo
SERVERLESS_FAST_MODE = os.getenv("SERVERLESS_FAST_MODE", "0") == "1"


# ===================================================================
# CONFIGURAÇÃO HYDE (INDEPENDENTE DO FAST_MODE)
# ===================================================================
# HyDE está DESLIGADO por padrão
# Para habilitar, defina USE_HYDE=1 no .env
USE_HYDE = os.getenv("USE_HYDE", "0") == "1"


# ===================================================================
# ⚡ OTIMIZAÇÃO: CONTROLE DE EXECUÇÃO DO RAG
# ===================================================================
# Por padrão, RAG está DESABILITADO no início do fluxo LATS-P
# Isto permite que LATS-P execute sem overhead de RAG
# RAG pode ser ativado:
#   - Manualmente via state["_skip_rag"] = False
#   - Após HITL quando contexto externo é necessário
#   - Quando memória FAISS estiver habilitada
#
# Para SEMPRE executar RAG (comportamento anterior), defina SKIP_RAG_DEFAULT=0
SKIP_RAG_DEFAULT = os.getenv("SKIP_RAG_DEFAULT", "1") == "1"


# ===================================================================
# PARÂMETROS RAG
# ===================================================================
if FAST_MODE_ENABLED:
    # FAST MODE: Contexto menor
    RAG_HYDE_ENABLED = USE_HYDE  # Respeita flag independente
    RAG_BM25_K = 2  # Apenas 2 docs BM25
    RAG_SEMANTIC_K = 2  # Apenas 2 docs semânticos
    RAG_RERANK_TOP_N = 3  # Top 3 após rerank
    RAG_MAX_CONTEXT_LENGTH = 1000  # Caracteres máximos
else:
    # MODO NORMAL: Full RAG pipeline
    RAG_HYDE_ENABLED = USE_HYDE  # Respeita flag independente
    RAG_BM25_K = 5
    RAG_SEMANTIC_K = 5
    RAG_RERANK_TOP_N = 5
    RAG_MAX_CONTEXT_LENGTH = 3000


# ===================================================================
# PARÂMETROS LLM
# ===================================================================
if FAST_MODE_ENABLED:
    # FAST MODE: Tokens limitados
    LLM_MAX_TOKENS = 256
    LLM_TEMPERATURE = 0  # Mantém determinístico
else:
    # MODO NORMAL
    LLM_MAX_TOKENS = 1024
    LLM_TEMPERATURE = 0


# ===================================================================
# PARÂMETROS LATS-P
# ===================================================================
if FAST_MODE_ENABLED:
    # FAST MODE: Menos candidatos
    LATS_MAX_STEPS = 30  # Reduzir de 40
    LATS_TOP_FINAIS = 2  # Reduzir de 3
else:
    # MODO NORMAL
    LATS_MAX_STEPS = 40
    LATS_TOP_FINAIS = 3


# ⚠️ CRÍTICO: HITL NÃO É AFETADO PELO FAST_MODE
# Os thresholds de entropia SEMPRE usam os valores padrão
HITL_THRESHOLD_ENTROPIA = 1.3  # NUNCA MUDE ISSO NO FAST_MODE
HITL_THRESHOLD_SCORE = 0.55
HITL_THRESHOLD_UNIFORMIDADE = 0.10

# Filtragem de opções no modal HITL (UX - não afeta lógica)
HITL_MIN_PROB = 0.15  # Probabilidade mínima para mostrar opção
HITL_TOP_K = 3  # Máximo de opções a mostrar (pega top-k por probabilidade)


# ===================================================================
# FUNÇÃO DE DIAGNÓSTICO
# ===================================================================
def get_fast_mode_config() -> Dict[str, Any]:
    """Retorna configuração atual para debug."""
    return {
        "fast_mode_enabled": FAST_MODE_ENABLED,
        "rag": {
            "hyde_enabled": RAG_HYDE_ENABLED,
            "bm25_k": RAG_BM25_K,
            "semantic_k": RAG_SEMANTIC_K,
            "rerank_top_n": RAG_RERANK_TOP_N,
            "max_context_length": RAG_MAX_CONTEXT_LENGTH,
        },
        "llm": {
            "max_tokens": LLM_MAX_TOKENS,
            "temperature": LLM_TEMPERATURE,
        },
        "lats": {
            "max_steps": LATS_MAX_STEPS,
            "top_finais": LATS_TOP_FINAIS,
        },
        "hitl": {
            "threshold_entropia": HITL_THRESHOLD_ENTROPIA,
            "threshold_score": HITL_THRESHOLD_SCORE,
            "threshold_uniformidade": HITL_THRESHOLD_UNIFORMIDADE,
            "affected_by_fast_mode": False,  # SEMPRE FALSE
        },
    }


# ===================================================================
# LOG STARTUP (usando logging para compatibilidade com Vercel)
# ===================================================================
import logging

logger = logging.getLogger(__name__)

# ===================================================================
# LOG STARTUP
# ===================================================================
if SERVERLESS_FAST_MODE:
    logger.info("="*70)
    logger.info(" 🚀 SERVERLESS MODE ATIVO")
    logger.info("="*70)
    logger.info("❌ FAISS DISABLED - Nenhum índice vetorial será carregado")
    logger.info("❌ RAG BYPASS - Pipeline RAG completamente desabilitado")
    logger.info("✅ LATS-P ATIVO - Todas as heurísticas, poda e entropia mantidas")
    logger.info("✅ HITL ATIVO - Human-in-the-loop preservado")
    logger.info(f"✅ LATS max_steps: {LATS_MAX_STEPS}")
    logger.info(f"✅ LATS top_finais: {LATS_TOP_FINAIS}")
    logger.info(f"⚠️  HITL THRESHOLD: {HITL_THRESHOLD_ENTROPIA} (NÃO AFETADO)")
    logger.info("="*70)
elif FAST_MODE_ENABLED:
    hyde_status = "HABILITADO" if RAG_HYDE_ENABLED else "DESABILITADO"
    logger.info("="*70)
    logger.info(" ⚡ FAST_MODE ATIVADO")
    logger.info("="*70)
    logger.info(f"✅ HyDE: {hyde_status}")
    logger.info(f"✅ RAG K: {RAG_BM25_K} BM25 + {RAG_SEMANTIC_K} Semântico")
    logger.info(f"✅ Rerank Top-N: {RAG_RERANK_TOP_N}")
    logger.info(f"✅ Contexto máximo: {RAG_MAX_CONTEXT_LENGTH} chars")
    logger.info(f"✅ LLM max_tokens: {LLM_MAX_TOKENS}")
    logger.info(f"✅ LATS max_steps: {LATS_MAX_STEPS}")
    logger.info(f"✅ LATS top_finais: {LATS_TOP_FINAIS}")
    logger.info(f"⚠️  HITL THRESHOLD: {HITL_THRESHOLD_ENTROPIA} (NÃO AFETADO)")
    logger.info("="*70)
else:
    hyde_status = "habilitado" if RAG_HYDE_ENABLED else "desabilitado"
    logger.info(f"[FAST_MODE] Desabilitado. Usando configuração padrão (full performance).")
    logger.info(f"[HyDE] {hyde_status.capitalize()} (USE_HYDE={USE_HYDE})")
