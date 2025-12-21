# lats_sistema/evolution/validators/compare_versions.py

import json
from typing import Dict, Any, List
from copy import deepcopy


class TreeComparator:
    """
    Compara duas versões da árvore:
        - original
        - evoluída (v2)
    E gera um relatório com:
        - diferenças de estrutura
        - diferenças de perguntas
        - nós adicionados/removidos
        - reordenação de filhos
        - sinalizações de divisão
    """

    def __init__(self, arvore_original: Dict[str, Any], arvore_v2: Dict[str, Any]):
        self.orig = arvore_original
        self.v2 = arvore_v2

        self.index_orig = self._index_arvore(self.orig)
        self.index_v2 = self._index_arvore(self.v2)

    # ------------------------------------------------------------
    # Indexação simples da árvore inteira
    # ------------------------------------------------------------
    def _index_arvore(self, node: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        index = {}

        def rec(n):
            index[n["id"]] = n
            for f in n.get("subnodos", []):
                rec(f)

        rec(node)
        return index

    # ------------------------------------------------------------
    # Comparar perguntas originais vs. perguntas v2
    # ------------------------------------------------------------
    def comparar_perguntas(self) -> List[Dict[str, Any]]:
        diferencas = []

        for node_id, node_v2 in self.index_v2.items():
            node_orig = self.index_orig.get(node_id)
            if not node_orig:
                continue  # nó novo (tratado em outra função)

            pergunta_orig = node_orig.get("pergunta", "")
            pergunta_v2 = node_v2.get("pergunta", "")

            if pergunta_orig.strip() != pergunta_v2.strip():
                diferencas.append({
                    "node_id": node_id,
                    "pergunta_original": pergunta_orig,
                    "pergunta_nova": pergunta_v2
                })

        return diferencas

    # ------------------------------------------------------------
    # Encontrar nós adicionados e removidos
    # ------------------------------------------------------------
    def comparar_ids(self):
        orig_ids = set(self.index_orig.keys())
        v2_ids = set(self.index_v2.keys())

        novos = v2_ids - orig_ids
        removidos = orig_ids - v2_ids

        return {
            "novos_nos": list(novos),
            "nos_removidos": list(removidos)
        }

    # ------------------------------------------------------------
    # Comparar ordem dos filhos
    # ------------------------------------------------------------
    def comparar_ordenacao(self) -> List[Dict[str, Any]]:
        alteracoes = []

        for node_id, orig_node in self.index_orig.items():
            v2_node = self.index_v2.get(node_id)
            if not v2_node:
                continue

            filhos_orig = [f["id"] for f in orig_node.get("subnodos", [])]
            filhos_v2 = [f["id"] for f in v2_node.get("subnodos", [])]

            if filhos_orig != filhos_v2:
                alteracoes.append({
                    "node_id": node_id,
                    "ordem_original": filhos_orig,
                    "ordem_nova": filhos_v2
                })

        return alteracoes

    # ------------------------------------------------------------
    # Nós que receberam tag "sugerir_divisao"
    # ------------------------------------------------------------
    def nos_sugerir_divisao(self) -> List[str]:
        marcados = []

        for node_id, node in self.index_v2.items():
            if node.get("sugerir_divisao") is True:
                marcados.append(node_id)

        return marcados

    # ------------------------------------------------------------
    # Gerar relatório consolidado
    # ------------------------------------------------------------
    def gerar_relatorio(self) -> Dict[str, Any]:
        return {
            "alteracoes_perguntas": self.comparar_perguntas(),
            "alteracoes_estrutura_ids": self.comparar_ids(),
            "alteracoes_ordenacao": self.comparar_ordenacao(),
            "sugerir_divisao": self.nos_sugerir_divisao(),
        }

    # ------------------------------------------------------------
    # Gerar relatório markdown bonito
    # ------------------------------------------------------------
    def gerar_relatorio_markdown(self) -> str:
        diffs = self.gerar_relatorio()

        md = ["# 📘 Comparativo da Árvore Original vs. Árvore v2\n"]

        md.append("## 📝 1. Perguntas Alteradas\n")
        if diffs["alteracoes_perguntas"]:
            for d in diffs["alteracoes_perguntas"]:
                md.append(f"### • Nó `{d['node_id']}`\n")
                md.append(f"**Pergunta original:**\n> {d['pergunta_original']}\n")
                md.append(f"**Pergunta nova:**\n> {d['pergunta_nova']}\n")
        else:
            md.append("_Nenhuma pergunta alterada._\n")

        md.append("\n## 🧩 2. Nós adicionados/removidos\n")
        md.append(f"**Novos nós:** {diffs['alteracoes_estrutura_ids']['novos_nos']}\n")
        md.append(f"**Nós removidos:** {diffs['alteracoes_estrutura_ids']['nos_removidos']}\n")

        md.append("\n## 🔀 3. Mudança na ordem dos filhos\n")
        if diffs["alteracoes_ordenacao"]:
            for d in diffs["alteracoes_ordenacao"]:
                md.append(f"### • Nó `{d['node_id']}`\n")
                md.append(f"- Ordem original: {d['ordem_original']}\n")
                md.append(f"- Nova ordem: {d['ordem_nova']}\n")
        else:
            md.append("_Nenhuma reordenação detectada._\n")

        md.append("\n## ✂️ 4. Nós sugeridos para divisão\n")
        if diffs["sugerir_divisao"]:
            md.append(f"- {diffs['sugerir_divisao']}\n")
        else:
            md.append("_Nenhum nó sugerido para divisão._\n")

        return "\n".join(md)
