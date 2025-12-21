from lats_sistema.memory.db import insert_memory_simple, get_decision_by_id
from lats_sistema.memory.faiss_store import add_vector, search_vectors
from lats_sistema.memory.memory_retriever import buscar_justificativas_semelhantes
from lats_sistema.models.embeddings import embeddings
import numpy as np

#from lats_sistema.memory.db import init_db; init_db()

def test_memory_pipeline():

    print("\n==============================")
    print("🧪 TESTE MANUAL DO SISTEMA DE MEMÓRIA")
    print("==============================\n")

    # ---------------------------------------------------------
    # 1) Criar um evento fictício + justificativa humana
    # ---------------------------------------------------------
    event_text = "Durante a troca de mangote, colaborador sofreu escoriação na mão direita."
    node_id = "lesao_forca_trabalho"
    chosen_child = "lesao_forca_trabalho_confirmada"
    human_j = "O modelo estava certo, pois houve lesão relacionada ao trabalho."

    print("📌 Inserindo memória no SQLite...")

    mem_id = insert_memory_simple(
        event_text=event_text,
        node_id=node_id,
        chosen_child=chosen_child,
        justification_human=human_j
    )

    print(f"✔️ Inserido no DB com id={mem_id}")

    # ---------------------------------------------------------
    # 2) Gerar embedding e guardar no FAISS
    # ---------------------------------------------------------
    print("\n📌 Gerando embedding...")
    vec = embeddings.embed_query(event_text)
    vec = np.array(vec).astype("float32")

    print("📌 Inserindo embedding no FAISS...")
    add_vector(vec, mem_id)

    # ---------------------------------------------------------
    # 3) Recuperar via FAISS + SQLite
    # ---------------------------------------------------------
    print("\n📌 Testando busca por similaridade...")

    resultados = buscar_justificativas_semelhantes(
        descricao_evento="Um trabalhador sofreu leve lesão na mão ao puxar uma mangueira.",
        node_id="lesao_forca_trabalho",
        k=3
    )

    print("\n📌 RESULTADOS ENCONTRADOS:")
    if not resultados:
        print("❌ Nenhuma memória encontrada.")
    else:
        for r in resultados:
            print("-" * 30)
            print(f"🆔 Evento armazenado: {r['event_text']}")
            print(f"➡️ Filho escolhido: {r['chosen_child']}")
            print(f"📝 Justificativa humana: {r['justification_human']}")


if __name__ == "__main__":
    test_memory_pipeline()






