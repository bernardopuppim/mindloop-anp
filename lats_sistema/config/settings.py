import os
import httpx
import configparser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ============================
# Localização robusta do projeto
# ============================
# settings.py está em:
# lats_sistema/config/settings.py
#
# Queremos chegar até:
# KG_MD/config.ini
#
BASE_DIR = Path(__file__).resolve().parents[2]   # sobe 2 níveis a partir de config/

CONFIG_FILE = BASE_DIR / "config.ini"
CA_CERT_FILE = BASE_DIR / "petrobras-ca-root.pem"

# ============================
# 🚀 MODO SERVERLESS: Usar env vars quando config.ini não existe
# ============================
SERVERLESS_FAST_MODE = os.getenv("SERVERLESS_FAST_MODE", "0") == "1"

# ============================
# Carregar config.ini (apenas se existir)
# ============================
config = configparser.ConfigParser()

if CONFIG_FILE.exists():
    # Modo local: carregar do config.ini
    config.read(CONFIG_FILE)

    if "AZURE" not in config:
        raise KeyError(
            f"[ERRO] Seção [AZURE] não existe em {CONFIG_FILE}.\n"
            f"Seções encontradas: {config.sections()}"
        )

    # Variáveis do config.ini
    AZURE_API_KEY = config["AZURE"]["API_KEY"]
    AZURE_ENDPOINT = config["AZURE"]["ENDPOINT"]
    AZURE_API_VERSION = config["AZURE"].get("API_VERSION", "2025-01-01-preview")
    AZURE_DEPLOYMENT_NAME = config["AZURE"].get("DEPLOYMENT_NAME", "")
    AZURE_CA_CERT_PATH = str(CA_CERT_FILE)

    logger.info(f"[CONFIG] Carregado de {CONFIG_FILE}")

elif SERVERLESS_FAST_MODE:
    # Modo serverless: usar variáveis de ambiente
    AZURE_API_KEY = os.getenv("AZURE_API_KEY", "")
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2025-01-01-preview")
    AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "")
    AZURE_CA_CERT_PATH = ""  # Não usado em serverless

    logger.info("[CONFIG] Modo serverless - usando variáveis de ambiente")

else:
    # Modo local sem config.ini: erro
    raise FileNotFoundError(
        f"[ERRO] config.ini não encontrado no caminho: {CONFIG_FILE}\n"
        f"DICA: Ele deve estar no diretório raiz do projeto (ex.: KG_MD/config.ini).\n"
        f"Ou defina SERVERLESS_FAST_MODE=1 para usar variáveis de ambiente."
    )


# ============================
# Cliente HTTP com CA correto
# ============================
def get_http_client():
    """
    Retorna cliente HTTP com certificado CA (modo local) ou padrão (serverless).
    """
    if SERVERLESS_FAST_MODE:
        # Modo serverless: usar certificados padrão do sistema
        logger.info("[HTTP CLIENT] Modo serverless - usando certificados padrão")
        return httpx.Client()

    # Modo local: usar CA customizado
    if not CA_CERT_FILE.exists():
        raise FileNotFoundError(
            f"[ERRO] Certificado CA não encontrado: {CA_CERT_FILE}."
        )
    return httpx.Client(verify=str(CA_CERT_FILE))
