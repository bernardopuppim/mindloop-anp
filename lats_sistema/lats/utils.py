# lats/utils.py
import math
from typing import List, Dict, Any

# --------------------------------------------
# Nó terminal da árvore
# --------------------------------------------
def eh_terminal(node: Dict[str, Any]) -> bool:
    return node.get("tipo") == "terminal" or "classe" in node


# --------------------------------------------
# Formatação dos filhos para o prompt do LLM
# --------------------------------------------
def formatar_filhos(node: Dict[str, Any]) -> str:
    linhas = []
    for f in node.get("subnodos", []):
        linhas.append(
            f"- id: {f['id']} | tipo: {f.get('tipo','')} | "
            f"classe: {f.get('classe','-')} | pergunta: {f.get('pergunta','')}"
        )
    return "\n".join(linhas)


# --------------------------------------------
# Softmax com temperatura
# --------------------------------------------
def softmax(scores: List[float], temperature: float = 0.7) -> List[float]:
    if not scores:
        return []
    temperature = max(temperature, 1e-3)
    exps = [math.exp(s / temperature) for s in scores]
    s = sum(exps)
    return [e/s for e in exps] if s > 0 else [1/len(scores)] * len(scores)


# --------------------------------------------
# Temperatura dinâmica: cresce com a profundidade
# --------------------------------------------
def temperatura_por_profundidade(depth: int) -> float:
    base = 0.4
    incremento = 0.12 * (depth - 1)
    return min(base + incremento, 1.2)


# --------------------------------------------
# Normalização de log_prob → distribuição de prob
# --------------------------------------------
def normalizar_log_probs(log_probs: List[float]) -> List[float]:
    if not log_probs:
        return []
    max_log = max(log_probs)
    exps = [math.exp(lp - max_log) for lp in log_probs]
    Z = sum(exps)
    return [e/Z for e in exps] if Z else [1/len(exps)] * len(exps)


# --------------------------------------------
# Entropia de Shannon
# --------------------------------------------
def shannon_entropy(probs: List[float]) -> float:
    H = 0.0
    for p in probs:
        if p > 0:
            H -= p * math.log(p, 2)
    return H
