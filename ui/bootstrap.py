# ================================================================
# streamlit/bootstrap.py
# ---------------------------------------------------------------
# Garante que a pasta raiz (onde está lats_sistema) esteja no sys.path
# para toda a aplicação Streamlit.
# ================================================================

import os
import sys

# Caminho da raíz do projeto (pai da pasta streamlit)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
