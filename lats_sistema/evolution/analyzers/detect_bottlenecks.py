# lats_sistema/evolution/analyzers/detect_bottlenecks.py

from typing import Dict, Any, List
from evolution.metrics.entropy_tracker import EntropyTracker


class BottleneckDetector:
    """
    Analisa estatísticas do EntropyTracker para identificar:

    - Nós com alta entropia (perguntas confusas)
    - Nós com baixa visitação (estruturas esquecidas)
    - Nós com entropia alta + baixa visitação (gargalos graves)
    - Nós onde há empate frequente entre alternativas (confusão estrutural)
    """

    def __init__(self, tracker: EntropyTracker):
        self.tracker = tracker
        self.stats_no = tracker.resumo_por_no()
        self.global_data = tracker.relatorio_global()

    # ---------------------------------------------------------------------
    # 1) Identificar nós de alta entropia
    # ---------------------------------------------------------------------
    def nos_alta_entropia(self, limiar: float = 1.2) -> List[Dict[str, Any]]:
        """
        Retorna nós com entropia média acima de um limiar.
        Em árvores de decisão, entropia > 1.2 bits já sugere ambiguidade.
        """

        resultados = []
        for node_id, data in self.stats_no.items():
            if data["media_entropia"] >= limiar:
                resultados.append({
                    "node_id": node_id,
                    "media_entropia": data["media_entropia"],
                    "desvio": data["desvio"],
                    "visitas": data["visitas"]
                })

        return sorted(resultados, key=lambda x: -x["media_entropia"])

    # ---------------------------------------------------------------------
    # 2) Nós com baixa visitação
    # ---------------------------------------------------------------------
    def nos_pouco_visitados(self, limiar: int = 5) -> List[Dict[str, Any]]:
        """
        Nós com menos visitas que o limiar são candidatos a revisão estrutural.
        """

        resultados = []
        for node_id, data in self.stats_no.items():
            if data["visitas"] < limiar:
                resultados.append({
                    "node_id": node_id,
                    "visitas": data["visitas"],
                    "media_entropia": data["media_entropia"]
                })

        return sorted(resultados, key=lambda x: x["visitas"])

    # ---------------------------------------------------------------------
    # 3) Nós com entropia alta + poucas visitas (gargalos graves)
    # ---------------------------------------------------------------------
    def gargalos_graves(self) -> List[Dict[str, Any]]:
        """
        Combinação crítica:
        - entropia média alta
        - poucos casos passam pelo nó
        Sugere que a pergunta está mal posicionada ou mal formulada.
        """

        resultados = []
        for node_id, data in self.stats_no.items():
            if data["visitas"] < 10 and data["media_entropia"] > 1.0:
                resultados.append({
                    "node_id": node_id,
                    "visitas": data["visitas"],
                    "media_entropia": data["media_entropia"]
                })

        return sorted(resultados, key=lambda x: -x["media_entropia"])

    # ---------------------------------------------------------------------
    # 4) Gerar relatório consolidado
    # ---------------------------------------------------------------------
    def gerar_relatorio(self) -> Dict[str, Any]:
        return {
            "total_nos": len(self.stats_no),
            "total_registros": self.global_data["total_registros"],

            "alta_entropia": self.nos_alta_entropia(),
            "pouco_visitados": self.nos_pouco_visitados(),
            "gargalos_graves": self.gargalos_graves()
        }
