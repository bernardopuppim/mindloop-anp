from lats_sistema.vectorstore.faiss_loader import load_faiss_store

def buscar_semantico(query):
    store = load_faiss_store()
    if store is None:
        return []  # RAG desativado
    return store.similarity_search(query, k=4)
