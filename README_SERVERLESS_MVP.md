# 🚀 Branch: serverless_mvp

**Objetivo**: Backend minimalista para Vercel Serverless (< 250 MB)

---

## 🎯 Diferenças do Branch `main`

| Aspecto | `main` | `serverless_mvp` |
|---------|--------|------------------|
| **RAG/FAISS** | ✅ Completo | ❌ Removido |
| **Dependências** | Completas (faiss, torch, langchain-community) | ✅ Minimalistas |
| **Bundle Size** | ~500 MB | < 100 MB ✅ |
| **LATS-P** | ✅ 100% | ✅ 100% (INALTERADO) |
| **HITL** | ✅ 100% | ✅ 100% (INALTERADO) |
| **Deploy Vercel** | ❌ Falha (limite 250 MB) | ✅ Sucesso |
| **Uso** | Desenvolvimento local com RAG | Produção serverless |

---

## ✅ O Que Foi Mantido (100%)

- ✅ **LATS-P completo** - Todas as heurísticas, poda, entropia
- ✅ **HITL** - Human-in-the-loop preservado (thresholds inalterados)
- ✅ **Classificação** - Mesma lógica de decisão
- ✅ **Prompts** - Inalterados
- ✅ **API FastAPI** - Mesmos endpoints e contratos
- ✅ **Justificativa técnica** - LLM gera explicações completas

---

## ❌ O Que Foi Removido

### Dependências Removidas

```diff
- faiss-cpu>=1.8.0          # ~180 MB
- langchain-community        # Inclui FAISS
- langchain (monolítico)     # Substituído por subpacotes
- rank-bm25>=0.2.2          # Busca BM25
- numpy>=1.26.0             # Dependência FAISS
- pandas>=2.2.0             # Manipulação dados
- streamlit>=1.40.0         # UI local
- loguru>=0.7.2             # Logging (usa logging padrão)
- tqdm>=4.66.0              # Progress bars
```

### Funcionalidades Removidas

- ❌ RAG (Retrieval-Augmented Generation)
- ❌ FAISS (busca semântica vetorial)
- ❌ HyDE (hipothetical document embeddings)
- ❌ BM25 Search
- ❌ Reranker
- ❌ Corpus normativo local

---

## 📦 Dependências Mantidas (Minimalistas)

```txt
# LLM (apenas subpacotes essenciais)
langchain-core>=0.3.0
langchain-openai>=0.2.0
langgraph>=0.2.0

# FastAPI
fastapi>=0.115.0
uvicorn>=0.30.0

# HTTP e Config
httpx>=0.27.0
certifi>=2024.0.0
python-dotenv>=1.0.0
pydantic>=2.10.0
```

**Bundle estimado**: < 100 MB (bem abaixo do limite de 250 MB)

---

## 🔧 Configuração

### Variáveis de Ambiente (Vercel Dashboard)

```bash
# Modo serverless (CRÍTICO)
SERVERLESS_FAST_MODE=1

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

# Opcional: Fast mode
FAST_MODE=1
USE_HYDE=0
SKIP_RAG_DEFAULT=1
```

---

## 🚀 Deploy no Vercel

### 1. Conectar Repositório

```bash
# No GitHub, selecione o branch: serverless_mvp
```

### 2. Configurar Variáveis de Ambiente

No Vercel Dashboard → Settings → Environment Variables:

```
SERVERLESS_FAST_MODE=1
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
```

### 3. Deploy

```bash
# Push para o branch
git push origin serverless_mvp

# Vercel auto-deploya ou use CLI
vercel --prod
```

### 4. Verificar

```bash
# Health check
curl https://seu-app.vercel.app/

# Esperado: {"status": "ok"}
```

---

## 🧪 Teste Local

### Instalação

```bash
# Instalar dependências minimalistas
pip install -r requirements.txt
```

### Executar

```bash
# Definir env vars
export SERVERLESS_FAST_MODE=1
export OPENAI_API_KEY=sk-...

# Rodar FastAPI
uvicorn backend.main:app --reload

# Acessar
# http://localhost:8000
# http://localhost:8000/docs
```

### Logs Esperados

```
======================================================================
 🚀 SERVERLESS MODE ATIVO
======================================================================
❌ FAISS DISABLED - Nenhum índice vetorial será carregado
❌ RAG BYPASS - Pipeline RAG completamente desabilitado
✅ LATS-P ATIVO - Todas as heurísticas, poda e entropia mantidas
✅ HITL ATIVO - Human-in-the-loop preservado
======================================================================
```

---

## 📊 Arquitetura Serverless

### Fluxo de Classificação

```
1. POST /api/predict
   ↓
2. [RAG BYPASS] → contexto_normativo = ""
   ↓
3. LATS-P (classificação via LLM + tree search)
   ↓
4. HITL (se entropia > threshold)
   ↓
5. Resposta JSON com classificação + justificativa
```

### O Que NÃO Muda

- ✅ Árvore de decisão (arvore_lats.json) - mesma
- ✅ Prompts de classificação - mesmos
- ✅ Heurísticas LATS-P - mesmas
- ✅ Thresholds HITL - mesmos
- ✅ Lógica de poda - mesma
- ✅ Cálculo de entropia - mesmo

---

## ⚠️ Limitações vs `main`

| Recurso | `main` | `serverless_mvp` |
|---------|--------|------------------|
| **Contexto normativo** | ✅ RAG busca documentos relevantes | ❌ Sem contexto externo |
| **Precisão** | Alta (LLM + RAG) | Moderada (apenas LLM) |
| **Resposta** | ~3-5s (com RAG) | ~2-3s (sem RAG) |
| **Bundle** | 500 MB | < 100 MB |
| **Deploy** | ❌ Falha Vercel | ✅ Sucesso |

**Recomendação**:
- `serverless_mvp`: Demos, MVPs, testes rápidos, produção com custo baixo
- `main`: Desenvolvimento local, produção com alta precisão (servidor dedicado)

---

## 📁 Estrutura de Arquivos

```
ANP_classifier/
├── api/
│   └── main.py              # Entrypoint Vercel
├── backend/
│   ├── main.py              # FastAPI app
│   └── services/
│       └── lats_service.py  # Lógica LATS-P
├── lats_sistema/
│   ├── config/
│   │   ├── fast_mode.py     # SERVERLESS_FAST_MODE flag
│   │   └── settings.py      # Config via env vars
│   ├── graph/
│   │   ├── build.py         # Grafo LangGraph
│   │   └── nodes.py         # Nós (RAG bypassado)
│   ├── lats/
│   │   ├── engine.py        # ✅ LATS-P (INALTERADO)
│   │   └── tree_loader.py   # ✅ Árvore (INALTERADO)
│   └── models/
│       ├── llm.py           # ✅ LLM lazy loading
│       └── llm_factory.py   # ✅ OpenAI factory
├── requirements.txt         # ✅ Minimalista (9 pacotes)
├── vercel.json              # ✅ SERVERLESS_FAST_MODE=1
├── .vercelignore            # ✅ Exclusões (data/, *.faiss, etc.)
└── README_SERVERLESS_MVP.md # Este arquivo
```

---

## 🔄 Sincronização com `main`

### Quando Atualizar `serverless_mvp`

Sempre que houver mudanças em **lógica de negócio** no `main`:

```bash
# No branch serverless_mvp
git merge main

# Resolver conflitos (se houver)
# - Manter requirements.txt do serverless_mvp
# - Manter vercel.json do serverless_mvp
# - Aceitar mudanças de lógica do main

git commit
git push origin serverless_mvp
```

### O Que NÃO Trazer do `main`

- ❌ Mudanças em requirements.txt (se adicionarem FAISS/RAG)
- ❌ Mudanças que desabilitam SERVERLESS_FAST_MODE
- ❌ Imports de langchain-community

---

## 🎯 Checklist de Deploy

Antes de fazer deploy, verificar:

- [ ] Branch correto (`serverless_mvp`)
- [ ] `SERVERLESS_FAST_MODE=1` em vercel.json
- [ ] requirements.txt SEM faiss-cpu, langchain-community
- [ ] .vercelignore exclui data/, notebooks/, *.faiss
- [ ] api/main.py existe e importa backend.main.app
- [ ] Variáveis de ambiente configuradas no Vercel

---

## 📝 Histórico de Mudanças

### 2025-12-21 - Criação do Branch

- ✅ Removidas dependências pesadas (faiss, torch, langchain-community)
- ✅ requirements.txt reduzido de 11 para 9 pacotes essenciais
- ✅ vercel.json configurado com SERVERLESS_FAST_MODE=1
- ✅ Documentação completa criada
- ✅ Testes de validação passando

---

## 🆘 Troubleshooting

### Erro: "No module named 'faiss'"

**Causa**: Código tentando importar FAISS

**Solução**: Verificar que `SERVERLESS_FAST_MODE=1` está configurado ANTES dos imports

### Erro: "Bundle size exceeds 250 MB"

**Causa**: Dependências pesadas no requirements.txt

**Solução**:
1. Verificar que está no branch `serverless_mvp`
2. Confirmar requirements.txt minimalista
3. Verificar .vercelignore excluindo data/, notebooks/

### Erro: "ModuleNotFoundError: langchain_community"

**Causa**: Código importando langchain_community (removido)

**Solução**: Lazy imports condicionais já implementados em nodes.py - verificar SERVERLESS_FAST_MODE

---

## 📚 Documentação Adicional

- [SERVERLESS_MODE.md](SERVERLESS_MODE.md) - Detalhes técnicos do modo serverless
- [VERCEL_DEPLOY_CHANGES.md](VERCEL_DEPLOY_CHANGES.md) - Mudanças para Vercel
- [VERCEL_ENTRYPOINT_FIX.md](VERCEL_ENTRYPOINT_FIX.md) - Fix de entrypoint

---

**Branch**: `serverless_mvp`
**Status**: ✅ Pronto para deploy
**Bundle**: < 100 MB
**Compatibilidade**: Vercel Serverless
**Lógica**: 100% LATS-P + HITL preservados
