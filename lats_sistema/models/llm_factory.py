# ================================================================
# lats_sistema/models/llm_factory.py
# Factory para criação de modelos LLM e Embeddings (OpenAI)
# ================================================================

import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
)

# ================================================================
# CARREGAR VARIÁVEIS DE AMBIENTE
# ================================================================
try:
    from dotenv import load_dotenv
    dotenv_available = True
except ImportError:
    dotenv_available = False

try:
    from lats_sistema.config.settings import BASE_DIR
except ImportError:
    BASE_DIR = Path(__file__).resolve().parents[2]

if dotenv_available:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)

# ================================================================
# CONFIGURAÇÕES OPENAI
# ================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# Performance
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# Validação
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY não encontrada no .env. "
        "Configure: OPENAI_API_KEY=sk-..."
    )

# ================================================================
# IMPORTS
# ================================================================
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# ================================================================
# CACHE (Singleton)
# ================================================================
_chat_model_cache = {}
_embed_model_cache = {}

# ================================================================
# FAST_MODE
# ================================================================
from lats_sistema.config.fast_mode import FAST_MODE_ENABLED, LLM_MAX_TOKENS

# ================================================================
# FACTORY: CHAT MODEL
# ================================================================
def get_chat_model(force_json: bool = False):
    """
    Retorna ChatOpenAI configurado.

    Args:
        force_json: Se True, força resposta em JSON

    Returns:
        ChatOpenAI instance
    """
    cache_key = f"openai_{force_json}"

    if cache_key in _chat_model_cache:
        return _chat_model_cache[cache_key]

    # Configuração base
    config = {
        "model": OPENAI_CHAT_MODEL,
        "temperature": 0,
        "timeout": LLM_TIMEOUT,
        "max_retries": LLM_MAX_RETRIES,
    }

    # FAST_MODE: limitar tokens
    if FAST_MODE_ENABLED:
        config["max_tokens"] = LLM_MAX_TOKENS

    # JSON mode
    if force_json:
        config["model_kwargs"] = {"response_format": {"type": "json_object"}}

    model = ChatOpenAI(**config)

    logging.info(
        f"✓ ChatOpenAI criado | model={OPENAI_CHAT_MODEL} | "
        f"json={force_json} | fast_mode={FAST_MODE_ENABLED}"
    )

    _chat_model_cache[cache_key] = model
    return model


# ================================================================
# FACTORY: EMBEDDINGS
# ================================================================
def get_embedding_model():
    """
    Retorna OpenAIEmbeddings configurado.

    Returns:
        OpenAIEmbeddings instance
    """
    cache_key = "openai_embeddings"

    if cache_key in _embed_model_cache:
        return _embed_model_cache[cache_key]

    model = OpenAIEmbeddings(
        model=OPENAI_EMBED_MODEL,
        timeout=LLM_TIMEOUT,
        max_retries=LLM_MAX_RETRIES,
    )

    logging.info(f"✓ OpenAIEmbeddings criado | model={OPENAI_EMBED_MODEL}")

    _embed_model_cache[cache_key] = model
    return model


# ================================================================
# EXPORTS
# ================================================================
__all__ = ["get_chat_model", "get_embedding_model"]
