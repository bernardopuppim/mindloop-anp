# lats_sistema/utils/confidence.py
"""
Traduz log_prob (valor técnico) em nível de confiança compreensível.
"""

from typing import Dict, Any


def traduzir_confianca(log_prob: float) -> Dict[str, Any]:
    """
    Converte log_prob em nível de confiança qualitativo.

    Args:
        log_prob: Log-probabilidade do caminho (negativo, mais próximo de 0 = melhor)

    Returns:
        dict com:
            - nivel: "alta" | "moderada" | "baixa"
            - emoji: str
            - cor: str (para UI)
            - descricao: str explicativa
            - valor_numerico: float (para logs técnicos)
    """

    # Mapeamento baseado em análise empírica
    if log_prob >= -1.0:
        return {
            "nivel": "alta",
            "emoji": "🟢",
            "cor": "green",
            "descricao": "O sistema identificou um caminho muito consistente e alinhado com os critérios normativos.",
            "valor_numerico": log_prob,
        }
    elif log_prob >= -2.5:
        return {
            "nivel": "moderada",
            "emoji": "🟡",
            "cor": "yellow",
            "descricao": "A decisão foi construída a partir do caminho mais consistente segundo os critérios normativos analisados.",
            "valor_numerico": log_prob,
        }
    else:
        return {
            "nivel": "baixa",
            "emoji": "🟠",
            "cor": "orange",
            "descricao": "O sistema encontrou algumas incertezas ao longo da classificação. Recomenda-se revisão.",
            "valor_numerico": log_prob,
        }


def formatar_resultado_usuario(node_id: str, log_prob: float, classe: str = None) -> str:
    """
    Formata mensagem final para o usuário de forma compreensível.

    Args:
        node_id: ID do nó final
        log_prob: Log-probabilidade
        classe: Classe final (opcional, extraído do nó se não fornecido)

    Returns:
        str: Mensagem formatada para exibição
    """
    conf = traduzir_confianca(log_prob)

    if not classe:
        classe = node_id  # Fallback

    mensagem = f"""
🔎 Resultado sugerido pelo sistema: {classe}
{conf['emoji']} Nível de confiança: {conf['nivel'].capitalize()}

ℹ️  {conf['descricao']}
"""

    return mensagem.strip()


def get_confianca_badge(log_prob: float) -> Dict[str, str]:
    """
    Retorna badge visual para UI (cor, texto).

    Uso em frontend:
        badge = get_confianca_badge(result.log_prob)
        <Badge color={badge['cor']}>{badge['texto']}</Badge>

    Args:
        log_prob: Log-probabilidade

    Returns:
        dict com 'cor' e 'texto'
    """
    conf = traduzir_confianca(log_prob)

    return {
        "cor": conf["cor"],
        "texto": f"{conf['emoji']} Confiança {conf['nivel'].capitalize()}",
        "nivel": conf["nivel"],
    }
