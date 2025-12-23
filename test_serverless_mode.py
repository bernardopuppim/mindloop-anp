#!/usr/bin/env python3
"""
Script de validação do modo serverless.

IMPORTANTE: Este script deve ser executado com SERVERLESS_FAST_MODE=1
JÁ CONFIGURADO antes do import (simula ambiente Vercel).

Testa que:
1. Imports condicionais funcionam
2. RAG é automaticamente bypassado
3. FAISS não é carregado (verificação via placeholders)
"""

import os
import sys

# 🚀 CRÍTICO: Configurar ANTES de qualquer import
# Simula o que acontece no Vercel (env var já existe no startup)
os.environ["SERVERLESS_FAST_MODE"] = "1"
os.environ["OPENAI_API_KEY"] = "sk-test-key"  # Necessário para não falhar validação

print("="*70)
print("🧪 TESTE: Modo Serverless - Validação de Imports")
print("="*70)
print(f"SERVERLESS_FAST_MODE = {os.getenv('SERVERLESS_FAST_MODE')}")
print("="*70)

# ===================================================================
# TESTE 1: Imports Condicionais
# ===================================================================
print("\n📋 TESTE 1: Imports Condicionais (RAG bypassado)")
print("-"*70)

try:
    from lats_sistema.config.fast_mode import SERVERLESS_FAST_MODE
    print(f"✅ SERVERLESS_FAST_MODE = {SERVERLESS_FAST_MODE}")

    from lats_sistema.graph.nodes import no_rag
    print("✅ Import de no_rag bem-sucedido")

    # Verificar que funções RAG são placeholders (None)
    from lats_sistema.graph import nodes

    placeholders_ok = (
        nodes.hyde_generate is None and
        nodes.buscar_bm25 is None and
        nodes.buscar_semantico is None and
        nodes.rerank is None and
        nodes.sintetizar is None and
        nodes.carregar_corpus_normativo is None
    )

    if placeholders_ok:
        print("✅ Todas as funções RAG são placeholders (None)")
        print("   → hyde_generate = None")
        print("   → buscar_bm25 = None")
        print("   → buscar_semantico = None")
        print("   → rerank = None")
        print("   → sintetizar = None")
        print("   → carregar_corpus_normativo = None")
    else:
        print("❌ ERRO: Algumas funções RAG não são None")
        print(f"   hyde_generate = {nodes.hyde_generate}")
        print(f"   buscar_bm25 = {nodes.buscar_bm25}")
        sys.exit(1)

    print("\n✅ TESTE 1 PASSOU: Imports condicionais funcionam corretamente")

except Exception as e:
    print(f"❌ ERRO no TESTE 1: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===================================================================
# TESTE 2: Bypass do RAG
# ===================================================================
print("\n📋 TESTE 2: Bypass Automático do Nó RAG")
print("-"*70)

try:
    state = {"descricao_evento": "Teste de vazamento"}
    result = no_rag(state)

    if result.get("contexto_normativo") == "":
        print("✅ RAG bypassado corretamente (contexto vazio)")
    else:
        print("❌ ERRO: RAG deveria ter sido bypassado")
        sys.exit(1)

    print("✅ TESTE 2 PASSOU: RAG bypass automático funciona")

except Exception as e:
    print(f"❌ ERRO no TESTE 2: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===================================================================
# RESULTADO FINAL
# ===================================================================
print("\n" + "="*70)
print("🎉 TODOS OS TESTES PASSARAM")
print("="*70)
print("✅ Modo serverless está funcionando corretamente")
print("✅ FAISS não é importado quando SERVERLESS_FAST_MODE=1")
print("✅ RAG é automaticamente bypassado")
print("✅ Código pronto para deploy no Vercel")
print("="*70)
