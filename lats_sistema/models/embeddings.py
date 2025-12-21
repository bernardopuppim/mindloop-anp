# lats_sistema/models/embeddings.py
"""
Módulo de acesso ao modelo de embeddings.
Usa factory pattern com OpenAI exclusivo.
Lazy loading para compatibilidade com serverless (Vercel).
"""

from lats_sistema.models.llm_factory import get_embedding_model

# Lazy loading via __getattr__ para compatibilidade com imports existentes
_cache = {}

def __getattr__(name):
    """Lazy load de embeddings"""
    if name == "embeddings":
        if "embeddings" not in _cache:
            _cache["embeddings"] = get_embedding_model()
        return _cache["embeddings"]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
