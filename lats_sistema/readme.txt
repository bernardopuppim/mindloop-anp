lats_sistema/
│
├── app.py                         # Arquivo principal (inicia o grafo)
│
├── config/
│   └── settings.py                # Carrega config.ini, CA, paths etc.
│
├── models/
│   ├── llm.py                     # Define llm_text, llm_json
│   └── embeddings.py              # Função load_embedding_model
│
├── vectorstore/
│   ├── faiss_loader.py            # Carrega o índice FAISS
│   └── corpus_loader.py           # Carrega arquivos .md + chunking
│
├── rag/
│   ├── hyde.py                    # HyDE
│   ├── bm25_search.py             # Busca lexical
│   ├── semantic_search.py         # Busca semântica FAISS
│   ├── reranker.py                # LLM-judge
│   └── synthesizer.py             # Síntese final
│
├── lats/
│   ├── state.py                   # TypedDicts
│   ├── utils.py                   # softmax, entropia, etc
│   ├── tree_loader.py             # árvore + NODE_INDEX + ROOT_ID
│   ├── evaluator.py               # avaliar_filhos_llm
│   └── engine.py                  # executar_lats
│
└── graph/
    ├── nodes.py                   # no_rag_contextualizador, no_classificar
    └── build.py                   # constrói o grafo LangGraph