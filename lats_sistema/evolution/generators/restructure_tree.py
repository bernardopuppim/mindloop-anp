# lats_sistema/evolution/generators/restructure_tree.py
"""
Gera uma árvore v2 (draft) com base nas métricas de entropia.

Não modifica a árvore original — apenas adiciona anotações:
- _diagnostico (entropia, visitas, status)
- _sugestao (texto geral)
- _propostas_llm (melhoria de pergunta / splits sugeridos)
"""

import json
from copy import deepcopy
from typing import Dict, Any

from lats_sistema.evolution.generators.improve_questions import (
    sugerir_melhoria_pergunta
)


def gerar_arvore_v2(arvore_original: Dict[str, Any],
                    resumo_por_no: Dict[str, Dict[str, float]],
                    threshold: float = 0.95) -> Dict[str, Any]:
    """
    Produz uma versão anotada da árvore, destacando nós problemáticos
    com entropia alta e incluindo propostas do LLM para melhorar as perguntas.
    """

    arv_v2 = deepcopy(arvore_original)

    def marcar_recursivo(node: Dict[str, Any]):
        node_id = node["id"]

        if node_id in resumo_por_no:
            stats = resumo_por_no[node_id]
            ent = stats["media_entropia"]
            visitas = stats["visitas"]

            status = (
                "problema_alto_ruido" if ent >= threshold else
                "ok" if visitas > 0 else
                "nao_visitado"
            )

            node["_diagnostico"] = {
                "entropia_media": ent,
                "visitas": visitas,
                "status": status,
            }

            # sugere ação macro
            if status == "problema_alto_ruido":
                node["_sugestao"] = "Nó com alta entropia: revisar pergunta e estrutura dos filhos."
                # 🔥 AQUI entra o LLM: propor nova pergunta / splits
                propostas = sugerir_melhoria_pergunta(
                    node=node,
                    entropia_media=ent,
                    visitas=visitas,
                )
                node["_propostas_llm"] = propostas

            elif status == "nao_visitado":
                node["_sugestao"] = "Nó nunca visitado: possivelmente obsoleto; avaliar remoção."
            else:
                node["_sugestao"] = "Nó está estável; nenhuma ação obrigatória."

        # recursão nos filhos
        for sub in node.get("subnodos", []):
            marcar_recursivo(sub)

    marcar_recursivo(arv_v2)
    return arv_v2


def salvar_arvore_v2(arvore_v2, caminho_out):
    with open(caminho_out, "w", encoding="utf-8") as f:
        json.dump(arvore_v2, f, indent=2, ensure_ascii=False)
