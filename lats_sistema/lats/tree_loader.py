import os
import json

# Diretório raiz do projeto (2 níveis acima deste arquivo)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Caminho correto para o arquivo JSON da árvore (na raiz do projeto)
TREE_PATH = os.path.join(BASE_DIR, "arvore_lats.json")

# Lazy loading: árvore só é carregada quando acessada
# Importante para cold start no Vercel
_cache = {}

def _load_tree():
    """Carrega a árvore do JSON (executado apenas uma vez)"""
    if "tree_loaded" in _cache:
        return

    with open(TREE_PATH, encoding="utf-8") as f:
        _cache["ARVORE"] = json.load(f)

    # Construir índice de nós
    _cache["NODE_INDEX"] = {}

    def index_nodes(node):
        _cache["NODE_INDEX"][node["id"]] = node
        for sub in node.get("subnodos", []):
            index_nodes(sub)

    index_nodes(_cache["ARVORE"])
    _cache["ROOT_ID"] = _cache["ARVORE"]["id"]
    _cache["tree_loaded"] = True

def __getattr__(name):
    """Lazy load de ARVORE, NODE_INDEX e ROOT_ID"""
    if name in ("ARVORE", "NODE_INDEX", "ROOT_ID"):
        _load_tree()
        return _cache[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
