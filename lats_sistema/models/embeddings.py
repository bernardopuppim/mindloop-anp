# lats_sistema/models/embeddings.py
"""
Módulo de acesso ao modelo de embeddings.
Usa factory pattern com OpenAI exclusivo.
"""

from lats_sistema.models.llm_factory import get_embedding_model

# Instanciar modelo usando factory
embeddings = get_embedding_model()
