# lats_sistema/evolution/generators/improve_questions.py
"""
Gera propostas de melhoria de perguntas para nós com alta entropia,
utilizando LLM.

Saída esperada: um dicionário com, por exemplo:
{
  "nova_pergunta": "...",
  "justificativa": "...",
  "novos_filhos_sugeridos": [
    {
      "titulo": "...",
      "descricao_criterio": "...",
      "exemplos": ["...", "..."]
    }
  ]
}
"""

from typing import Dict, Any, List
from lats_sistema.models.llm import llm_json  # ou llm_text se preferir


PROMPT_MELHORIA = """
Você é um especialista em classificação de incidentes de SMS (Segurança, Meio Ambiente e Saúde)
trabalhando em uma Árvore de Decisão normativa.

Receberá informações sobre UM nó da árvore que está apresentando ALTA ENTROPIA
(ou seja, as decisões a partir dele estão muito ambíguas).

INFORMAÇÕES DO NÓ:
- ID do nó: {node_id}
- Pergunta atual: {pergunta_atual}
- Classe associada (se houver): {classe_atual}
- Entropia média observada: {entropia_media:.3f}
- Número de visitas (eventos que passaram por esse nó): {visitas}

OBJETIVO:
1) Propor uma NOVA formulação de pergunta para tornar esse nó mais discriminativo.
2) Opcionalmente, sugerir uma divisão do nó em 2-4 filhos, com critérios mais claros.
3) Para cada filho sugerido, descreva:
   - Um título curto
   - Um critério objetivo de classificação
   - 1 a 3 exemplos de incidentes típicos que cairiam nesse filho.

Restrições:
- A pergunta deve ser clara, objetiva e alinhada com incidentes de SMS.
- Sempre que possível, use linguagem operacional (campo, embarcação, manutenção, etc.).

FORMATO DE RESPOSTA (APENAS JSON VÁLIDO):

{{
  "nova_pergunta": "<texto da nova pergunta>",
  "justificativa": "<explicação breve do porquê esta pergunta é melhor>",
  "novos_filhos_sugeridos": [
    {{
      "titulo": "<nome curto do filho>",
      "descricao_criterio": "<critério objetivo de classificação>",
      "exemplos": ["exemplo 1", "exemplo 2"]
    }}
  ]
}}
"""


def sugerir_melhoria_pergunta(
    node: Dict[str, Any],
    entropia_media: float,
    visitas: int,
) -> Dict[str, Any]:
    """
    Usa LLM para propor uma nova pergunta e possíveis splits para o nó.
    Se houver erro no LLM, retorna um dicionário mínimo com sugestão genérica.
    """

    pergunta = node.get("pergunta", "")
    classe = node.get("classe", "Classe_indefinida")

    prompt = PROMPT_MELHORIA.format(
        node_id=node["id"],
        pergunta_atual=pergunta or "(sem pergunta definida)",
        classe_atual=classe,
        entropia_media=entropia_media,
        visitas=visitas,
    )

    try:
        resp = llm_json.invoke(prompt)
        raw = resp.content.strip()

        # Proteção para ```json
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()

        import json
        data = json.loads(raw)

        # Normalização leve
        return {
            "nova_pergunta": data.get("nova_pergunta", "").strip(),
            "justificativa": data.get("justificativa", "").strip(),
            "novos_filhos_sugeridos": data.get("novos_filhos_sugeridos", []),
        }

    except Exception as e:
        # fallback defensivo
        return {
            "nova_pergunta": pergunta,
            "justificativa": f"Falha ao consultar LLM ({e}); manter pergunta original, revisar manualmente.",
            "novos_filhos_sugeridos": [],
        }
