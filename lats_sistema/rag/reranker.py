import json
from langchain_core.prompts import ChatPromptTemplate
from lats_sistema.models.llm import llm_json
from lats_sistema.utils.json_utils import invoke_json

# ⚡ OTIMIZAÇÃO: Threshold para bypass do rerank LLM
# Se há apenas 1 candidato ou poucos candidatos, rerank LLM é desnecessário
RERANK_MIN_CANDIDATES = 2  # Mínimo de candidatos para valer a pena reranking

prompt_rerank = ChatPromptTemplate.from_template("""
Reranqueie os trechos conforme relevância ao evento:

EVENTO:
{evento}

TRECHOS:
{trechos}

JSON:
{{
 "ranking": [
   {{"trecho": "...", "score": 0.0}}
 ]
}}
""")

def rerank(evento, trechos, force_llm: bool = False):
    """
    Rerank de trechos RAG com bypass condicional para performance.

    ⚡ OTIMIZAÇÃO: Se há <= 1 candidato, não faz rerank LLM (economiza tokens).

    Args:
        evento: Descrição do evento
        trechos: Lista de trechos (strings ou dicts)
        force_llm: Se True, força rerank LLM mesmo com poucos candidatos

    Returns:
        Lista de dicts {" trecho": str, "score": float} ordenada por relevância
    """
    # Normalizar trechos para strings
    trechos_norm = []
    for t in trechos:
        if isinstance(t, str):
            trechos_norm.append(t)
        elif isinstance(t, dict) and "trecho" in t:
            trechos_norm.append(t["trecho"])
        else:
            trechos_norm.append(str(t))

    # ⚡ BYPASS 1: Se há <= 1 candidato, retornar diretamente
    if len(trechos_norm) <= RERANK_MIN_CANDIDATES and not force_llm:
        print(f"⚡ Rerank BYPASS: apenas {len(trechos_norm)} candidato(s), retornando sem LLM")
        return [{"trecho": t, "score": 1.0 - i*0.1} for i, t in enumerate(trechos_norm)]

    # Rerank LLM padrão
    print(f"🔄 Rerankiando {len(trechos_norm)} candidatos com LLM...")
    trechos_fmt = "\n\n".join(f"[{i}] {t}" for i, t in enumerate(trechos_norm))

    full_prompt = prompt_rerank.format(
        evento=evento,
        trechos=trechos_fmt
    )

    try:
        data = invoke_json(
            llm_json,
            full_prompt,
            max_retries=2,
            schema_hint='{"ranking": [{"trecho": "...", "score": 0.0}]}'
        )
    except Exception as e:
        print(f"[ERRO] Rerank JSON inválido: {e}")
        # Fallback: retornar ordem original com scores decrescentes
        return [{"trecho": t, "score": 1.0 - i*0.1} for i, t in enumerate(trechos_norm)]

    ranking = data.get("ranking", [])
    ranking.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return ranking
