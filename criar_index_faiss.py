# ================================================================
# 🧠 CRIAR ÍNDICE FAISS PARA PADRÕES / NORMAS PETROBRAS
# ================================================================
import os
import re
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

# Carregar variáveis de ambiente
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

# ================================================================
# 1. CARREGAR EMBEDDINGS — MESMO MODELO DO SISTEMA LATS
# ================================================================
from lats_sistema.models.llm_factory import get_embedding_model

embeddings = get_embedding_model()
print(f"✓ Usando modelo: {os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')}")


# ================================================================
# 2. CARREGAR DOCUMENTOS .md DO DIRETÓRIO
# ================================================================
def carregar_md(dir_path="padroes_petrobras"):
    docs = []

    if not os.path.isdir(dir_path):
        raise Exception(f"Diretório não encontrado: {dir_path}")

    for filename in os.listdir(dir_path):
        # Ignorar arquivos de checkpoint do Jupyter
        if filename.startswith('.') or '-checkpoint' in filename:
            continue

        if filename.lower().endswith(".md"):
            fpath = os.path.join(dir_path, filename)

            with open(fpath, "r", encoding="utf-8") as f:
                texto = f.read().strip()

            # Sanitização simples
            texto = texto.replace("```", "")
            texto = re.sub(r"<[^>]+>", "", texto)

            if texto:
                docs.append(Document(page_content=texto, metadata={"source": filename}))

    print(f"✓ Carregados {len(docs)} documentos .md de {dir_path}")
    return docs


# ================================================================
# 3. QUEBRAR DOCUMENTOS EM CHUNKS (RECOMENDADO PARA RAG)
# ================================================================
def chunk_documentos(docs, chunk_size=900, chunk_overlap=150):
    chunks = []
    for doc in docs:
        texto = doc.page_content
        palavras = texto.split()

        for i in range(0, len(palavras), chunk_size - chunk_overlap):
            trecho = " ".join(palavras[i : i + chunk_size])
            chunks.append(Document(
                page_content=trecho,
                metadata=doc.metadata
            ))

    print(f"Total de chunks gerados: {len(chunks)}")
    return chunks


# ================================================================
# 4. CONSTRUIR ÍNDICE FAISS
# ================================================================
def construir_faiss(docs, save_path="data/faiss/index_anp"):
    print("🔄 Gerando embeddings e criando índice FAISS...")

    # Criar diretório se não existir
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    store = FAISS.from_documents(docs, embeddings)
    store.save_local(save_path)
    print(f"✅ Índice FAISS salvo em: {save_path}")


# ================================================================
# 5. EXECUTAR PIPELINE COMPLETA
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 RECRIANDO ÍNDICE FAISS COM OPENAI EMBEDDINGS")
    print("=" * 60)

    docs = carregar_md()
    chunks = chunk_documentos(docs)
    construir_faiss(chunks)

    print("\n✅ CONCLUÍDO! Índice compatível com OpenAI criado.")
