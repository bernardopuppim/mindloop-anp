# lats_sistema/config/logging_config.py
"""
Configuração centralizada de logging para compatibilidade com Vercel.
"""

import logging
import sys

# Configurar logging para funcionar bem no Vercel
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Vercel captura stdout
    ]
)

def get_logger(name: str) -> logging.Logger:
    """Retorna logger configurado para o módulo"""
    return logging.getLogger(name)
