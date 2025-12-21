# lats_sistema/evolution/metrics/entropy_tracker.py
import math
from typing import Dict, List, Any
from collections import defaultdict


class EntropyTracker:
    """
    Calcula estatísticas de entropia com base no full tracking do LATS-P.

    Cada entrada deve ser um histórico completo como retornado por:
    - state["final"]["principal"]["percurso_completo"]
    - state["final"]["top3"][i]["percurso_completo"]
    """

    def __init__(self):
        # Guarda entropias por node_id
        self.entropia_nos = defaultdict(list)

        # Guarda entropia por profundidade
        self.entropia_por_depth = defaultdict(list)

        # Número de vezes que cada nó foi visitado
        self.visitas = defaultdict(int)

        # Armazena todas as amostras
        self.registros = []

    # ===========================================================
    # FUNÇÕES AUXILIARES
    # ===========================================================
    @staticmethod
    def shannon_entropy(probs: List[float]) -> float:
        """Entropia de Shannon padrão (em bits)."""
        return -sum(p * math.log2(p) for p in probs if p > 0)

    @staticmethod
    def normalizar(scores: List[float]) -> List[float]:
        """Normaliza scores para virar distribuição de probabilidade."""
        total = sum(scores)
        if total == 0:
            return [1 / len(scores)] * len(scores)
        return [s / total for s in scores]

    # ===========================================================
    # PROCESSAMENTO DE UM CAMINHO COMPLETO DO LATS-P
    # ===========================================================
    def processar_percurso(self, percurso: List[Dict[str, Any]]):
        """
        Recebe o percurso completo do LATS-P e atualiza estatísticas.
        """

        for etapa in percurso:
            if "children" not in etapa:
                # última etapa (folha)
                continue

            node_id = etapa["node_id_atual"]
            depth = etapa.get("profundidade", 0)
            children = etapa["children"]

            # registra visita
            self.visitas[node_id] += 1

            # extrai distribuição de probabilidade dos filhos avaliados
            probs = [c["prob"] for c in children]
            probs = self.normalizar(probs)

            # calcula entropia
            H = self.shannon_entropy(probs)

            # guarda para estatísticas posteriores
            self.entropia_nos[node_id].append(H)
            self.entropia_por_depth[depth].append(H)

            # guarda registro bruto
            self.registros.append({
                "node_id": node_id,
                "depth": depth,
                "probs": probs,
                "entropia": H,
                "children": children
            })

    # ===========================================================
    # RELATÓRIOS
    # ===========================================================
    def resumo_por_no(self) -> Dict[str, Dict[str, float]]:
        """Retorna média, desvio e visitas por nó."""

        resumo = {}
        for node_id, valores in self.entropia_nos.items():
            if not valores:
                continue

            media = sum(valores) / len(valores)
            variancia = sum((h - media)**2 for h in valores) / len(valores)
            desvio = math.sqrt(variancia)

            resumo[node_id] = {
                "media_entropia": media,
                "desvio": desvio,
                "visitas": self.visitas[node_id]
            }

        return resumo

    def resumo_por_profundidade(self) -> Dict[int, Dict[str, float]]:
        """Retorna estatísticas de entropia por profundidade da árvore."""

        resumo = {}
        for depth, valores in self.entropia_por_depth.items():
            if not valores:
                continue

            media = sum(valores) / len(valores)
            variancia = sum((h - media)**2 for h in valores) / len(valores)
            desvio = math.sqrt(variancia)

            resumo[depth] = {
                "media_entropia": media,
                "desvio": desvio,
                "samples": len(valores)
            }

        return resumo

    # ===========================================================
    # RELATÓRIO GLOBAL consolidado
    # ===========================================================
    def relatorio_global(self) -> Dict[str, Any]:
        return {
            "total_registros": len(self.registros),
            "nos_avaliados": len(self.entropia_nos),
            "resumo_por_no": self.resumo_por_no(),
            "resumo_por_profundidade": self.resumo_por_profundidade()
        }
