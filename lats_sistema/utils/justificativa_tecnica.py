# lats_sistema/utils/justificativa_tecnica.py
"""
Geração de justificativa técnica formal via LLM.

Produz texto no estilo de parecer técnico regulatório,
adequado para comunicação à ANP, sem mencionar o funcionamento interno do sistema.
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from lats_sistema.models.llm import llm_text
from lats_sistema.lats.tree_loader import NODE_INDEX


def extrair_informacoes_factuais(historico: List[Dict[str, Any]], node_id_final: str) -> Dict[str, str]:
    """
    Extrai informações factuais consolidadas do caminho percorrido.

    Args:
        historico: Lista de decisões tomadas
        node_id_final: ID do nó final

    Returns:
        Dict com informações factuais consolidadas
    """
    info = {
        "tipo_ocorrencia": "",
        "produto": "",
        "volume": "",
        "impacto": "",
        "lesoes": "",
        "afastamento": "",
        "outros_detalhes": [],
    }

    # Percorrer histórico para extrair fatos
    for decisao in historico:
        node_id = decisao.get("node_id", "")
        escolhido = decisao.get("chosen_child", "")
        node = NODE_INDEX.get(node_id, {})
        node_escolhido = NODE_INDEX.get(escolhido, {})

        pergunta = node.get("pergunta", "")
        resposta = node_escolhido.get("pergunta", "")

        # Tipo de ocorrência (primeira decisão)
        if "tipo de ocorrência" in pergunta.lower() or node_id == "raiz":
            if "lesao" in escolhido.lower() and "forca" in escolhido.lower():
                info["tipo_ocorrencia"] = "acidente com lesão na força de trabalho"
            elif "lesao" in escolhido.lower() and "comunidade" in escolhido.lower():
                info["tipo_ocorrencia"] = "acidente com lesão em membro da comunidade"
            elif "meio_ambiente" in escolhido.lower():
                info["tipo_ocorrencia"] = "acidente com impacto no meio ambiente"
            elif "patrimonio" in escolhido.lower():
                info["tipo_ocorrencia"] = "acidente com dano ao patrimônio"
            elif "doenca" in escolhido.lower():
                info["tipo_ocorrencia"] = "doença ocupacional"
            elif "incidente" in escolhido.lower():
                info["tipo_ocorrencia"] = "incidente"

        # Produto (se mencionado)
        if "produto" in pergunta.lower() or "diesel" in resposta.lower():
            if "diesel" in escolhido.lower() or "diesel" in resposta.lower():
                info["produto"] = "óleo diesel"
            elif "perigoso" in escolhido.lower():
                info["produto"] = "produto perigoso"

        # Volume (se mencionado)
        if "volume" in pergunta.lower() or "m³" in pergunta.lower():
            if "10" in pergunta or "10" in resposta:
                info["volume"] = "10 m³"
            elif "100" in escolhido.lower():
                info["volume"] = "até 100 m³"

        # Impacto ambiental
        if "ambiental" in pergunta.lower() or "meio ambiente" in pergunta.lower():
            if "contaminação" in resposta.lower():
                info["impacto"] = "contaminação ambiental"
            elif "corpo hídrico" in resposta.lower() or "corpo d'água" in resposta.lower():
                info["impacto"] = "impacto em corpo hídrico"

        # Lesões
        if "lesão" in pergunta.lower() or "afastamento" in pergunta.lower():
            if "primeiros socorros" in pergunta.lower():
                info["lesoes"] = "lesão de primeiros socorros"
            elif "tratamento médico" in pergunta.lower():
                info["lesoes"] = "lesão com tratamento médico"
            elif "permanente" in pergunta.lower():
                info["lesoes"] = "lesão permanente"

        # Afastamento (dias)
        if "dias" in pergunta.lower() or "afastamento" in pergunta.lower():
            if "200" in escolhido.lower():
                info["afastamento"] = "entre 200 e 3.000 dias"
            elif "3000" in escolhido.lower():
                info["afastamento"] = "acima de 3.000 dias"
            elif "menos" in escolhido.lower():
                info["afastamento"] = "menos de 200 dias"

    return info


prompt_justificativa = ChatPromptTemplate.from_template("""
Você é um especialista em regulamentação ANP e está redigindo a justificativa técnica para a classificação de um evento.

**INSTRUÇÕES CRÍTICAS:**
- Escreva como um técnico responsável justificaria a decisão
- Utilize linguagem regulatória, objetiva e defensável
- NÃO mencione: árvores, nós, LATS, scores, probabilidades, sistema, ferramenta, algoritmo
- NÃO descreva o funcionamento interno da análise
- Escreva na terceira pessoa, impessoal
- Texto adequado para relatório à ANP

**ESTRUTURA OBRIGATÓRIA:**
1. Contextualização do evento (1-2 parágrafos)
2. Enquadramento técnico da ocorrência (1 parágrafo)
3. Justificativa objetiva para a classe atribuída (1 parágrafo)
4. Conclusão assertiva (1 parágrafo curto)

**EVENTO ANALISADO:**
{descricao_evento}

**CLASSE ATRIBUÍDA:**
{classe}

**INFORMAÇÕES FACTUAIS CONSOLIDADAS:**
- Tipo de ocorrência: {tipo_ocorrencia}
- Produto envolvido: {produto}
- Volume estimado: {volume}
- Impacto observado: {impacto}
- Lesões: {lesoes}
- Afastamento: {afastamento}

**REDIJA A JUSTIFICATIVA TÉCNICA:**
""")


def gerar_justificativa_tecnica_llm(
    descricao_evento: str,
    classe: str,
    historico: List[Dict[str, Any]],
    node_id_final: str,
) -> str:
    """
    Gera justificativa técnica formal via LLM.

    Produz texto no estilo de parecer técnico regulatório,
    adequado para comunicação à ANP.

    Args:
        descricao_evento: Descrição do evento fornecida pelo usuário
        classe: Classe final atribuída (ex: "Classe 3")
        historico: Lista de decisões tomadas durante LATS-P
        node_id_final: ID do nó final

    Returns:
        str: Justificativa técnica formatada
    """
    # Extrair informações factuais do caminho percorrido
    info = extrair_informacoes_factuais(historico, node_id_final)

    # Preparar prompt
    full_prompt = prompt_justificativa.format(
        descricao_evento=descricao_evento,
        classe=classe,
        tipo_ocorrencia=info.get("tipo_ocorrencia", "não especificado"),
        produto=info.get("produto", "não especificado"),
        volume=info.get("volume", "não especificado"),
        impacto=info.get("impacto", "não especificado"),
        lesoes=info.get("lesoes", "não aplicável"),
        afastamento=info.get("afastamento", "não aplicável"),
    )

    # Gerar justificativa via LLM
    try:
        response = llm_text.invoke(full_prompt)
        justificativa = response.content.strip()

        # Garantir que não mencione termos técnicos internos
        termos_proibidos = ["LATS", "nó", "árvore", "score", "probabilidade", "sistema", "ferramenta", "algoritmo"]
        for termo in termos_proibidos:
            if termo.lower() in justificativa.lower():
                # Fallback: remover menções
                justificativa = justificativa.replace(termo, "análise")
                justificativa = justificativa.replace(termo.lower(), "análise")

        return justificativa

    except Exception as e:
        print(f"⚠️ Erro ao gerar justificativa via LLM: {e}")
        # Fallback: texto genérico formal
        return gerar_justificativa_fallback(descricao_evento, classe, info)


def gerar_justificativa_fallback(
    descricao_evento: str,
    classe: str,
    info: Dict[str, str],
) -> str:
    """
    Gera justificativa fallback em caso de erro no LLM.

    Args:
        descricao_evento: Descrição do evento
        classe: Classe atribuída
        info: Informações factuais extraídas

    Returns:
        str: Justificativa genérica formal
    """
    tipo = info.get("tipo_ocorrencia", "evento")
    produto = info.get("produto", "")
    volume = info.get("volume", "")
    impacto = info.get("impacto", "")

    texto = f"""Com base na análise das informações disponíveis, verificou-se a ocorrência de {tipo}"""

    if produto:
        texto += f" envolvendo {produto}"

    texto += ".\n\n"

    if volume:
        texto += f"O volume estimado não contido foi da ordem de {volume}. "

    if impacto:
        texto += f"Constatou-se {impacto}. "

    texto += f"""

Considerando as características do evento, sua natureza, extensão e consequências, o enquadramento técnico aponta para a classificação como {classe}, conforme parâmetros normativos aplicáveis.

Dessa forma, a classificação atribuída reflete adequadamente a severidade e as consequências observadas no evento analisado."""

    return texto.strip()
