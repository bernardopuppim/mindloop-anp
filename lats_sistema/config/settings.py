import os
import httpx
import configparser
from pathlib import Path

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
# Carregar config.ini
# ============================
config = configparser.ConfigParser()

if not CONFIG_FILE.exists():
    raise FileNotFoundError(
        f"[ERRO] config.ini não encontrado no caminho: {CONFIG_FILE}\n"
        f"DICA: Ele deve estar no diretório raiz do projeto (ex.: KG_MD/config.ini)."
    )

config.read(CONFIG_FILE)

if "AZURE" not in config:
    raise KeyError(
        f"[ERRO] Seção [AZURE] não existe em {CONFIG_FILE}.\n"
        f"Seções encontradas: {config.sections()}"
    )

# ============================
# Variáveis exportadas
# ============================
AZURE_API_KEY = config["AZURE"]["API_KEY"]
AZURE_ENDPOINT = config["AZURE"]["ENDPOINT"]
AZURE_API_VERSION = config["AZURE"].get("API_VERSION", "2025-01-01-preview")
AZURE_DEPLOYMENT_NAME = config["AZURE"].get("DEPLOYMENT_NAME", "")
AZURE_CA_CERT_PATH = str(CA_CERT_FILE)


# ============================
# Cliente HTTP com CA correto
# ============================
def get_http_client():
    if not CA_CERT_FILE.exists():
        raise FileNotFoundError(
            f"[ERRO] Certificado CA não encontrado: {CA_CERT_FILE}."
        )
    return httpx.Client(verify=str(CA_CERT_FILE))
