# lats/evaluator.py
import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from lats_sistema.models.llm import llm_json
from lats_sistema.lats.utils import formatar_filhos
from lats_sistema.utils.json_utils import invoke_json

# ---------------------------------------------------------
# Avaliação via LLM – compara EVENTO vs FILHOS do nó atual
# ---------------------------------------------------------
def avaliar_filhos_llm(node: Dict[str, Any], descricao_evento: str, contexto_normativo: str):
    filhos = node.get("subnodos", [])
    if not filhos:
        return []

    filhos_formatados = formatar_filhos(node)
    contexto_normativo = contexto_normativo or ""

    prompt = ChatPromptTemplate.from_template("""
Você é um CLASSIFICADOR NORMATIVO PETROBRAS/ANP baseado em uma ÁRVORE DE DECISÃO.

==================================================================
TRECHOS DA RAG:
{contexto_normativo}

EVENTO:
{descricao_evento}

NÓ ATUAL:
ID: {node_id}
Pergunta: {pergunta_atual}

FILHOS:
{filhos_formatados}
==================================================================

Avalie CADA FILHO:

- Compatível → 0.6 a 1.0
- Incompatível → 0.0 a 0.1
- Incerteza → 0.2 a 0.4

Justificativa **sempre coerente com score**.

Retorne **apenas JSON**:

{{
  "avaliacoes": [
    {{"id": "...", "score": 0.0, "justificativa": "..."}}
  ]
}}
""")

    # Montar prompt completo
    full_prompt = prompt.format(
        contexto_normativo=contexto_normativo,
        descricao_evento=descricao_evento.strip(),
        node_id=node["id"],
        pergunta_atual=node.get("pergunta", ""),
        filhos_formatados=filhos_formatados,
    )

    # Usar invoke_json com retry automático
    try:
        data = invoke_json(
            llm_json,
            full_prompt,
            max_retries=2,
            schema_hint='{"avaliacoes": [{"id": "...", "score": 0.0, "justificativa": "..."}]}'
        )
    except Exception as e:
        print(f"[ERRO] JSON inválido em avaliar_filhos_llm após retries: {e}")
        return []

    aval = data.get("avaliacoes", [])
    if not isinstance(aval, list):
        return []

    out = []
    for a in aval:
        try:
            out.append({
                "id": str(a["id"]),
                "score": float(a.get("score", 0.0)),
                "justificativa": str(a.get("justificativa", "")),
            })
        except:
            continue

    return out
