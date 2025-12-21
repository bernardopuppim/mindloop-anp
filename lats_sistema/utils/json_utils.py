# lats_sistema/utils/json_utils.py
"""
Utilitários para garantir respostas JSON válidas dos LLMs.
Implementa retry automático e parsing robusto.
"""

import json
from typing import Any, Dict, Optional


def invoke_json(
    llm,
    prompt: str,
    max_retries: int = 2,
    schema_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invoca um LLM e garante que a resposta seja JSON válido.

    Args:
        llm: Instância do chat model (OpenAI ChatOpenAI)
        prompt: Prompt base do usuário
        max_retries: Número máximo de tentativas de correção
        schema_hint: String descrevendo o schema esperado (opcional)

    Returns:
        Dict parseado do JSON

    Raises:
        ValueError: Se após todas as tentativas ainda não conseguir JSON válido
    """

    # Adicionar instruções para forçar JSON
    json_instruction = "\n\nIMPORTANTE: Responda APENAS com JSON válido, sem texto adicional antes ou depois."

    if schema_hint:
        json_instruction += f"\n\nSchema esperado:\n{schema_hint}"

    full_prompt = prompt + json_instruction

    for attempt in range(max_retries + 1):
        try:
            # Invocar LLM
            response = llm.invoke(full_prompt)

            # Extrair conteúdo
            if hasattr(response, "content"):
                text = response.content
            elif isinstance(response, str):
                text = response
            else:
                text = str(response)

            # Limpar texto (remover markdown code blocks se houver)
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Tentar parse
            parsed = json.loads(text)
            return parsed

        except json.JSONDecodeError as e:
            if attempt < max_retries:
                # Retry com instrução de correção
                full_prompt = (
                    f"A resposta anterior não foi JSON válido. Erro: {e}\n\n"
                    f"Resposta anterior:\n{text}\n\n"
                    f"Por favor, corrija e retorne APENAS JSON válido sem texto adicional."
                )
            else:
                # Última tentativa falhou
                raise ValueError(
                    f"Falha ao obter JSON válido após {max_retries} tentativas.\n"
                    f"Último erro: {e}\n"
                    f"Última resposta: {text[:500]}"
                )

    raise ValueError("invoke_json: número de tentativas excedido (não deveria chegar aqui)")


def parse_json_safe(text: str, default: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Parse JSON de forma segura, retornando default em caso de erro.

    Args:
        text: String para fazer parse
        default: Valor default se parsing falhar (None por padrão)

    Returns:
        Dict parseado ou default
    """
    try:
        # Limpar texto
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)

    except (json.JSONDecodeError, ValueError):
        if default is not None:
            return default
        return {}
