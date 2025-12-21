# ============================================================
# lats/hitl_gating.py
# ------------------------------------------------------------
# Define a lógica que decide quando acionar o HITL
# ============================================================

import math
from typing import Dict, Any, List


# Parametrizações principais
THRESHOLD_ENTROPIA = 1.3          # limite para entropia local
THRESHOLD_SCORE = 0.55            # score mínimo aceitável do melhor filho
THRESHOLD_UNIFORMIDADE = 0.10     # diferença mínima entre prob mais alta e segunda


def shannon_entropy(probs: List[float]) -> float:
    """Entropia de Shannon padrão."""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def precisa_hitl(etapa: Dict[str, Any]) -> bool:
    """
    Decide se deve acionar o HITL (Human-in-the-Loop)
    com base na incerteza da etapa atual do LATS-P.

    REGRA CRÍTICA: HITL só é acionado se houver > 1 filho com score > 0

    Espera um dict com:
      - node_id: str
      - children: List[{"id", "score", "prob", ...}]
      - depth: int
      - entropia_local: float
    """

    filhos = etapa.get("children") or []
    if not filhos:
        return False

    # ===================================================================
    # FILTRO CRÍTICO: Apenas filhos válidos (score > 0)
    # ===================================================================
    filhos_validos = [c for c in filhos if c.get("score", 0) > 0]

    # Se há 0 ou 1 filho válido → decisão automática, SEM HITL
    if len(filhos_validos) <= 1:
        return False

    # Extrair scores e probs apenas dos válidos
    scores = [c["score"] for c in filhos_validos]
    probs = [c["prob"] for c in filhos_validos]

    # Normaliza defensivamente
    total = sum(probs)
    if total > 0:
        probs = [p / total for p in probs]

    # 1) Entropia local alta (calculada APENAS sobre válidos)
    entropia = shannon_entropy(probs)
    if entropia > THRESHOLD_ENTROPIA:
        return True

    # 2) Melhor score muito baixo
    if max(scores) < THRESHOLD_SCORE:
        return True

    # 3) Probabilidades muito próximas (achatadas)
    sorted_probs = sorted(probs, reverse=True)
    if len(sorted_probs) >= 2:
        if (sorted_probs[0] - sorted_probs[1]) < THRESHOLD_UNIFORMIDADE:
            return True

    return False


def gerar_hitl_metadata(node: Dict[str, Any], etapa: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai metadados necessários para o nó HITL.

    REGRAS:
    1. Filtra score == 0 PRIMEIRO (opções incompatíveis)
    2. Ordena por probabilidade
    3. Aplica top-k e threshold de probabilidade mínima
    """
    from lats_sistema.config.fast_mode import HITL_MIN_PROB, HITL_TOP_K

    filhos = etapa.get("children") or []

    # ===================================================================
    # FILTRO 1: Remover filhos com score == 0 (incompatíveis)
    # ===================================================================
    filhos_validos = [c for c in filhos if c.get("score", 0) > 0]

    if not filhos_validos:
        # Fallback de segurança (não deveria acontecer se precisa_hitl funcionou)
        return {
            "node_id": etapa.get("node_id"),
            "pergunta": node.get("pergunta", ""),
            "children": [],
            "depth": etapa.get("depth"),
            "entropia_local": 0.0,
        }

    # Recalcular probs apenas dos válidos
    probs = [c["prob"] for c in filhos_validos]
    total = sum(probs) or 1.0
    probs_norm = [p / total for p in probs]

    # ===================================================================
    # FILTRO 2: Ordenar por probabilidade (maior primeiro)
    # ===================================================================
    filhos_sorted = sorted(
        zip(filhos_validos, probs_norm),
        key=lambda x: x[1],
        reverse=True
    )

    # ===================================================================
    # FILTRO 3: Top-K e threshold de probabilidade mínima
    # ===================================================================
    filhos_relevantes = []
    for i, (filho, prob) in enumerate(filhos_sorted):
        # Sempre inclui top-K, independente do threshold
        if i < HITL_TOP_K:
            filhos_relevantes.append(filho)
        # Depois do top-K, só inclui se passar no threshold
        elif prob >= HITL_MIN_PROB:
            filhos_relevantes.append(filho)
        # Parar se prob ficar muito baixa
        else:
            break

    # Garantir que há pelo menos 1 opção (dos válidos)
    if not filhos_relevantes and filhos_sorted:
        filhos_relevantes = [filhos_sorted[0][0]]

    return {
        "node_id": etapa.get("node_id"),
        "pergunta": node.get("pergunta", ""),
        "children": filhos_relevantes,  # Apenas válidos, ordenados e filtrados
        "depth": etapa.get("depth"),
        "entropia_local": shannon_entropy(probs_norm),  # Entropia dos válidos
    }
