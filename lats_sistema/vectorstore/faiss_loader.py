from pathlib import Path
from langchain_community.vectorstores import FAISS
from lats_sistema.models.llm_factory import get_embedding_model

# Ajuste aqui se quiser outro path
INDEX_PATH = Path("data/faiss/index_anp")

faiss_store = None

def load_faiss_store():
    global faiss_store

    if faiss_store is not None:
        return faiss_store

    if not INDEX_PATH.exists():
        print(f"[FAISS] AVISO: índice não encontrado em {INDEX_PATH}. RAG desativado.")
        return None

    embeddings = get_embedding_model()

    faiss_store = FAISS.load_local(
        str(INDEX_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )

    print(f"[FAISS] Índice carregado com sucesso: {INDEX_PATH}")
    return faiss_store
