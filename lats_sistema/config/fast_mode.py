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
# LOG STARTUP
# ===================================================================
if FAST_MODE_ENABLED:
    print("\n" + "="*70)
    print(" ⚡ FAST_MODE ATIVADO")
    print("="*70)
    hyde_status = "HABILITADO" if RAG_HYDE_ENABLED else "DESABILITADO"
    print(f"✅ HyDE: {hyde_status}")
    print(f"✅ RAG K: {RAG_BM25_K} BM25 + {RAG_SEMANTIC_K} Semântico")
    print(f"✅ Rerank Top-N: {RAG_RERANK_TOP_N}")
    print(f"✅ Contexto máximo: {RAG_MAX_CONTEXT_LENGTH} chars")
    print(f"✅ LLM max_tokens: {LLM_MAX_TOKENS}")
    print(f"✅ LATS max_steps: {LATS_MAX_STEPS}")
    print(f"✅ LATS top_finais: {LATS_TOP_FINAIS}")
    print(f"\n⚠️  HITL THRESHOLD: {HITL_THRESHOLD_ENTROPIA} (NÃO AFETADO)")
    print("="*70 + "\n")
else:
    hyde_status = "habilitado" if RAG_HYDE_ENABLED else "desabilitado"
    print(f"[FAST_MODE] Desabilitado. Usando configuração padrão (full performance).")
    print(f"[HyDE] {hyde_status.capitalize()} (USE_HYDE={USE_HYDE})")
