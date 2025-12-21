# lats_sistema/utils/output_formatter.py
"""
Formatador de saída para apresentação profissional dos resultados LATS-P.

Transforma informações técnicas (IDs, log_prob, histórico) em uma apresentação
clara, limpa e orientada a decisão para o usuário final.
"""

from typing import Dict, Any, List, Optional
from lats_sistema.lats.tree_loader import NODE_INDEX
from lats_sistema.utils.justificativa_tecnica import gerar_justificativa_tecnica_llm


def extrair_classe_limpa(node_id: str) -> str:
    """
    Extrai o nome da classe de forma limpa, removendo IDs técnicos.

    Args:
        node_id: ID técnico do nó final (ex: "dias_200_3000_terminal")

    Returns:
        str: Classe limpa (ex: "Classe 4")

    Examples:
        >>> extrair_classe_limpa("dias_200_3000_terminal")
        "Classe 4"
        >>> extrair_classe_limpa("lesao_primeiros_socorros_confirma")
        "Classe 1"
    """
    node = NODE_INDEX.get(node_id, {})
    classe = node.get("classe", "")

    if classe:
        # Já está no formato limpo (ex: "Classe 1")
        return classe

    # Fallback: se não houver campo classe, tentar extrair do ID
    # (improvável, mas defensivo)
    if "classe_" in node_id.lower():
        # Ex: "incidente_classe_2" → "Classe 2"
        parts = node_id.lower().split("classe_")
        if len(parts) > 1:
            numero = parts[1].split("_")[0]
            return f"Classe {numero.upper()}"

    return "Classe não identificada"


def mapear_confianca_qualitativa(log_prob: float) -> Dict[str, Any]:
    """
    Mapeia log-probability para nível qualitativo de confiança.

    Usa os mesmos thresholds do sistema de confiança já implementado.

    Args:
        log_prob: Log-probability do caminho final

    Returns:
        Dict com:
            - nivel: "alta" | "moderada" | "baixa"
            - emoji: Ícone visual
            - cor: Cor para UI
            - descricao: Texto explicativo
    """
    if log_prob >= -1.0:
        return {
            "nivel": "alta",
            "emoji": "🟢",
            "cor": "green",
            "descricao": "Alta confiança no caminho de classificação",
            "nivel_display": "Alta",
        }
    elif log_prob >= -2.5:
        return {
            "nivel": "moderada",
            "emoji": "🟡",
            "cor": "yellow",
            "descricao": "Confiança moderada - decisão consistente com evidências disponíveis",
            "nivel_display": "Moderada",
        }
    else:
        return {
            "nivel": "baixa",
            "emoji": "🟠",
            "cor": "orange",
            "descricao": "Confiança baixa - recomenda-se revisão por especialista",
            "nivel_display": "Baixa",
        }


def gerar_tipo_ocorrencia(historico: List[Dict[str, Any]], node_id_final: str) -> str:
    """
    Gera descrição do tipo de ocorrência baseada no caminho percorrido.

    Args:
        historico: Lista de decisões tomadas durante LATS-P
        node_id_final: ID do nó final

    Returns:
        str: Descrição legível do tipo de ocorrência

    Examples:
        "Acidente com Lesão na Força de Trabalho"
        "Acidente com Impacto no Meio Ambiente"
        "Incidente sem classificação de gravidade"
    """
    if not historico:
        return "Tipo não determinado"

    # Primeira decisão geralmente define o tipo principal
    primeira_decisao = historico[0] if historico else {}
    escolha_raiz = primeira_decisao.get("chosen_child", "")

    # Mapeamento de IDs técnicos para descrições legíveis
    mapeamento_tipos = {
        "lesao_forca_trabalho": "Acidente com Lesão na Força de Trabalho",
        "lesao_comunidade": "Acidente com Lesão em Membro da Comunidade",
        "doenca_ocupacional": "Doença Ocupacional",
        "impacto_meio_ambiente": "Acidente com Impacto no Meio Ambiente",
        "dano_patrimonio": "Acidente com Dano ao Patrimônio",
        "perda_contencao": "Perda de Contenção com Foco em Segurança de Processo",
        "incidentes": "Incidente",
        "desvio": "Desvio",
    }

    # Buscar descrição
    for chave, descricao in mapeamento_tipos.items():
        if chave in escolha_raiz:
            return descricao

    # Fallback: tentar extrair do nó final
    node_final = NODE_INDEX.get(node_id_final, {})
    pergunta_final = node_final.get("pergunta", "")

    if pergunta_final:
        # Usar primeira pergunta como tipo
        return pergunta_final.split("?")[0]

    return "Tipo de ocorrência não especificado"


def gerar_resumo_tecnico(
    evento: str,
    historico: List[Dict[str, Any]],
    node_id_final: str,
    classe: str,
    log_prob: float,
) -> str:
    """
    Gera resumo técnico consolidado para auditoria e relatórios.

    Este texto é adequado para:
    - Auditoria regulatória
    - Relatórios gerenciais
    - Explicação para stakeholders

    Args:
        evento: Descrição do evento analisado
        historico: Lista de decisões tomadas
        node_id_final: ID do nó final
        classe: Classe final atribuída
        log_prob: Log-probability do resultado

    Returns:
        str: Resumo técnico formatado em markdown
    """
    confianca = mapear_confianca_qualitativa(log_prob)
    tipo_ocorrencia = gerar_tipo_ocorrencia(historico, node_id_final)

    # Construir narrativa do caminho lógico
    caminho_narrativo = _construir_narrativa_caminho(historico)

    # Extrair justificativas principais
    justificativas_principais = _extrair_justificativas_principais(historico)

    # Construir resumo
    resumo = f"""## 📋 Resumo Técnico da Classificação

### Evento Analisado
{evento}

### Tipo de Ocorrência Identificado
{tipo_ocorrencia}

### Classe Atribuída
**{classe}**

### Nível de Confiança
{confianca['emoji']} **{confianca['nivel_display']}** ({log_prob:.2f})

{confianca['descricao']}

### Caminho Lógico Percorrido

{caminho_narrativo}

### Justificativas Principais

{justificativas_principais}

### Decisões Consideradas
Total de **{len(historico)} etapas** de análise percorridas.

---

*Classificação gerada automaticamente pelo sistema LATS-P (Language Agent Tree Search - Probabilístico)*
"""

    return resumo


def _construir_narrativa_caminho(historico: List[Dict[str, Any]]) -> str:
    """
    Constrói narrativa legível do caminho percorrido na árvore.

    Args:
        historico: Lista de decisões

    Returns:
        str: Narrativa formatada
    """
    if not historico:
        return "_Nenhuma decisão intermediária registrada._"

    narrativa = []

    for i, decisao in enumerate(historico, 1):
        node_id = decisao.get("node_id", "")
        node = NODE_INDEX.get(node_id, {})
        pergunta = node.get("pergunta", "Decisão não especificada")

        escolhido = decisao.get("chosen_child", "")
        node_escolhido = NODE_INDEX.get(escolhido, {})
        resposta = node_escolhido.get("pergunta", escolhido)

        # Se foi colapso ontológico, indicar
        colapso = decisao.get("colapso_ontologico", False)
        marcador = "🔒" if colapso else f"{i}."

        # Formatar decisão
        narrativa.append(f"{marcador} **Decisão**: {pergunta}")

        if colapso:
            narrativa.append(f"   - ✅ Decisão determinística (colapso ontológico)")
        else:
            score = decisao.get("chosen_score", 0)
            prob = decisao.get("chosen_prob", 0)
            narrativa.append(f"   - ✅ Escolhido com {prob*100:.0f}% probabilidade (score: {score:.2f})")

        narrativa.append("")  # Linha em branco

    return "\n".join(narrativa)


def _extrair_justificativas_principais(historico: List[Dict[str, Any]]) -> str:
    """
    Extrai e formata as justificativas mais relevantes do modelo.

    Args:
        historico: Lista de decisões

    Returns:
        str: Justificativas formatadas
    """
    if not historico:
        return "_Nenhuma justificativa disponível._"

    justificativas = []

    for decisao in historico:
        # Buscar justificativa do caminho escolhido
        children = decisao.get("children", [])
        escolhido_id = decisao.get("chosen_child", "")

        for child in children:
            if child.get("id") == escolhido_id:
                just = child.get("justificativa", "")
                if just and just.strip():
                    justificativas.append(f"- {just.strip()}")
                break

        # Se houve justificativa humana (HITL), incluir
        just_humana = decisao.get("justificativa_humana", "")
        if just_humana and just_humana.strip():
            justificativas.append(f"- **[Decisão Humana]**: {just_humana.strip()}")

    if not justificativas:
        return "_Justificativas não registradas para este caminho._"

    return "\n".join(justificativas)


def formatar_saida_final(resultado_final: Dict[str, Any], descricao_evento: str) -> Dict[str, Any]:
    """
    Formata resultado final do LATS-P para apresentação profissional.

    Transforma dados técnicos em formato adequado para UI enterprise.

    Args:
        resultado_final: Dict com "final" do state LATS-P
            - node_id: ID técnico do nó final
            - log_prob: Log-probability do caminho
            - historico: Lista de decisões tomadas
        descricao_evento: Texto do evento analisado

    Returns:
        Dict com campos formatados:
            - classe: "Classe X" (limpo, sem IDs)
            - tipo_ocorrencia: Descrição legível
            - confianca: Dict com nivel, emoji, cor, descricao
            - num_decisoes: Número de etapas
            - justificativa_tecnica: Texto formal via LLM (estilo parecer ANP)
            - resumo_tecnico: Texto consolidado para auditoria (deprecated)
            - _raw: Dados brutos (para debug)
    """
    if not resultado_final or "node_id" not in resultado_final:
        return {
            "classe": "Não classificado",
            "tipo_ocorrencia": "Análise incompleta",
            "confianca": {
                "nivel": "baixa",
                "emoji": "⚠️",
                "cor": "red",
                "descricao": "Classificação não concluída",
                "nivel_display": "Indefinida",
            },
            "num_decisoes": 0,
            "resumo_tecnico": "Análise não foi concluída com sucesso.",
            "_raw": resultado_final,
        }

    node_id_final = resultado_final["node_id"]
    log_prob = resultado_final.get("log_prob", -999)
    historico = resultado_final.get("historico", [])

    # Extrair informações formatadas
    classe = extrair_classe_limpa(node_id_final)
    tipo_ocorrencia = gerar_tipo_ocorrencia(historico, node_id_final)
    confianca = mapear_confianca_qualitativa(log_prob)
    resumo_tecnico = gerar_resumo_tecnico(
        evento=descricao_evento,
        historico=historico,
        node_id_final=node_id_final,
        classe=classe,
        log_prob=log_prob,
    )

    # ✨ Gerar justificativa técnica formal via LLM
    print("📝 Gerando justificativa técnica via LLM...")
    justificativa_tecnica = gerar_justificativa_tecnica_llm(
        descricao_evento=descricao_evento,
        classe=classe,
        historico=historico,
        node_id_final=node_id_final,
    )

    return {
        "classe": classe,
        "tipo_ocorrencia": tipo_ocorrencia,
        "confianca": confianca,
        "num_decisoes": len(historico),
        "justificativa_tecnica": justificativa_tecnica,  # ✨ NOVO: Texto formal via LLM
        "resumo_tecnico": resumo_tecnico,  # Mantido para compatibilidade (deprecated)
        "_raw": resultado_final,  # Manter dados brutos para debug
    }
