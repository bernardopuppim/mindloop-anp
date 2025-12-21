# lats_sistema/evolution/analyzers/semantic_diagnosis.py

from typing import Dict, List, Any
from models.llm import llm_text  # usa o modelo de análise textual
from langchain_core.prompts import ChatPromptTemplate


class SemanticDiagnosis:
    """
    Diagnóstico semântico dos nós problemáticos.
    Usa o LLM para:
      - explicar por que o nó é confuso
      - analisar eventos reais que passam por esse nó
      - identificar inconsistências nas justificativas do LLM
      - sugerir causas semânticas da ambiguidade
    """

    def __init__(self, arvore, eventos_historicos):
        """
        arvore: dicionário da árvore inteira
        eventos_historicos: lista de dicts com formato final LATS-P
        """
        self.arvore = arvore
        self.eventos = eventos_historicos
        self.node_index = self._index_arvore(arvore)

    # ----------------------------------------------------------
    # UTILITÁRIOS
    # ----------------------------------------------------------
    def _index_arvore(self, node):
        index = {}

        def rec(n):
            index[n["id"]] = n
            for f in n.get("subnodos", []):
                rec(f)
        rec(node)
        return index

    # ----------------------------------------------------------
    # EXTRAÇÃO DE EXEMPLOS RELEVANTES
    # ----------------------------------------------------------
    def coletar_eventos_do_no(self, node_id, max_eventos=8):
        """
        Encontra no histórico todos os eventos cujo percurso 
        passou pelo node_id.
        """

        selecionados = []
        for ev in self.eventos:
            percurso = ev["final"]["principal"]["percurso_completo"]

            for etapa in percurso:
                if etapa.get("node_id_atual") == node_id:
                    selecionados.append(ev)
                    break

        # limita para não sobrecarregar o prompt
        return selecionados[:max_eventos]

    # ----------------------------------------------------------
    # DIAGNÓSTICO VIA LLM
    # ----------------------------------------------------------
    def diagnosticar_no(self, node_id):
        """
        Gera um diagnóstico semântico explicando:
        - por que o nó está confuso
        - como melhorar
        - que tipo de eventos caem lá
        - exemplos de decisões ambíguas
        """

        node = self.node_index[node_id]
        eventos = self.coletar_eventos_do_no(node_id)

        textos_exemplo = []
        for ev in eventos:
            textos_exemplo.append(ev["descricao_evento"])

        filhos_info = []
        for f in node.get("subnodos", []):
            filhos_info.append(f"- {f['id']}: {f.get('pergunta', '')}")

        prompt = ChatPromptTemplate.from_template("""
Você é um especialista em Engenharia de Segurança, SMS e normas ANP/Petrobras.
Seu papel é diagnosticar AMBIGUIDADES semânticas em nós de uma árvore de decisão normativa.

----------------------
NÓ ANALISADO:
ID: {node_id}
PERGUNTA:
{pergunta}

FILHOS:
{filhos_formatados}

----------------------
EXEMPLOS REAIS DE EVENTOS QUE PASSARAM POR ESTE NÓ:
{eventos_exemplo}

TAREFA:
1. Analise os exemplos reais.
2. Explique *por que* este nó pode estar gerando confusões, ambiguidades ou baixa separação entre ramos.
3. Identifique padrões semânticos que tornam difícil decidir entre os filhos.
4. Sugira melhorias concretas na formulação da pergunta.
5. Sugira melhorias de estrutura (ex.: mover filhos, dividir o nó, criar subperguntas).
6. Aponte que tipo de informação deveria ser adicionada nos eventos para melhorar a separação.
7. Seja objetivo, técnico e preciso.

FORMATO DA RESPOSTA:
{{
    "problemas_identificados": ["...", "..."],
    "sugestoes_melhoria_pergunta": ["...", "..."],
    "sugestoes_melhoria_estrutura": ["...", "..."],
    "informacoes_importantes_que_faltam": ["...", "..."],
    "observacoes_adicionais": "..."
}}
        """)

        chain = prompt | llm_text
        resp = chain.invoke({
            "node_id": node_id,
            "pergunta": node.get("pergunta", ""),
            "filhos_formatados": "\n".join(filhos_info),
            "eventos_exemplo": "\n\n---\n\n".join(textos_exemplo) if textos_exemplo else "Nenhum evento encontrado."
        })

        return resp.content

    # ----------------------------------------------------------
    # DIAGNÓSTICO EM LOTE
    # ----------------------------------------------------------
    def diagnosticar_varios(self, lista_nodes: List[str]) -> Dict[str, Any]:
        """
        Executa diagnóstico semântico para múltiplos nós.
        """

        resultados = {}
        for node_id in lista_nodes:
            resultados[node_id] = self.diagnosticar_no(node_id)
        return resultados
