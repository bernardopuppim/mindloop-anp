import os
import json

# Diretório raiz do projeto (2 níveis acima deste arquivo)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Caminho correto para o arquivo JSON da árvore (na raiz do projeto)
TREE_PATH = os.path.join(BASE_DIR, "arvore_lats.json")

# Carregar árvore
with open(TREE_PATH, encoding="utf-8") as f:
    ARVORE = json.load(f)

# Construção do índice de nós
NODE_INDEX = {}

def index_nodes(node):
    NODE_INDEX[node["id"]] = node
    for sub in node.get("subnodos", []):
        index_nodes(sub)

index_nodes(ARVORE)

ROOT_ID = ARVORE["id"]
