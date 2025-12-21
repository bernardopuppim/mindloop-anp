# lats_sistema/models/llm.py
"""
Módulo de acesso aos LLMs (text e json).
Usa factory pattern com OpenAI exclusivo.
"""

from lats_sistema.models.llm_factory import get_chat_model

# Instanciar modelos usando factory
llm_text = get_chat_model(force_json=False)
llm_json = get_chat_model(force_json=True)
