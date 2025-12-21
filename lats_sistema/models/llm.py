# lats_sistema/models/llm.py
"""
Módulo de acesso aos LLMs (text e json).
Usa factory pattern com OpenAI exclusivo.
Lazy loading para compatibilidade com serverless (Vercel).
"""

from lats_sistema.models.llm_factory import get_chat_model

# Lazy loading: modelos são criados via factory sob demanda
# O factory já implementa cache interno, então múltiplas chamadas
# retornam a mesma instância

def get_llm_text():
    """Retorna LLM para texto (lazy loaded via factory)"""
    return get_chat_model(force_json=False)

def get_llm_json():
    """Retorna LLM para JSON (lazy loaded via factory)"""
    return get_chat_model(force_json=True)

# Para compatibilidade com código existente que importa llm_text/llm_json
# diretamente, criamos apenas no primeiro acesso via __getattr__
_cache = {}

def __getattr__(name):
    """Lazy load de llm_text e llm_json"""
    if name == "llm_text":
        if "llm_text" not in _cache:
            _cache["llm_text"] = get_llm_text()
        return _cache["llm_text"]
    elif name == "llm_json":
        if "llm_json" not in _cache:
            _cache["llm_json"] = get_llm_json()
        return _cache["llm_json"]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
