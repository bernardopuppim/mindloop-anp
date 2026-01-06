# 🚀 Instruções de Deploy - Vercel

**Branch**: `serverless_mvp`
**Status**: ✅ Pronto para deploy

---

## 📋 Pré-requisitos

- [x] Código commitado no branch `serverless_mvp`
- [x] Pushed para GitHub
- [x] requirements.txt sem numpy/FAISS
- [x] vercel.json configurado
- [x] SERVERLESS_FAST_MODE=1

---

## 🌐 Opção 1: Deploy via Vercel Dashboard (Recomendado)

### Passo 1: Acessar Vercel

1. Acesse: https://vercel.com
2. Faça login com sua conta GitHub

### Passo 2: Importar Projeto

1. Click em **"Add New Project"**
2. Selecione o repositório: `bernardopuppim/mindloop-anp`
3. **IMPORTANTE**: Selecione o branch `serverless_mvp`

### Passo 3: Configurar Variáveis de Ambiente

No campo **Environment Variables**, adicione:

```bash
SERVERLESS_FAST_MODE=1
OPENAI_API_KEY=sk-proj-... (sua chave)
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
```

**Opcional (se usar Azure)**:
```bash
AZURE_API_KEY=...
AZURE_ENDPOINT=...
```

### Passo 4: Deploy

1. Click em **"Deploy"**
2. Aguarde o build (~2-3 minutos)
3. Vercel mostrará a URL do deploy

### Passo 5: Testar

```bash
# Health check
curl https://seu-app.vercel.app/

# Esperado: {"status": "ok"}
```

---

## 💻 Opção 2: Deploy via Vercel CLI

### Instalar Vercel CLI

```bash
npm install -g vercel
```

### Fazer Login

```bash
vercel login
```

### Deploy

```bash
# No diretório do projeto (branch serverless_mvp)
vercel --prod

# Vercel perguntará:
# Set up and deploy? [Y/n] → Y
# Which scope? → Selecione sua conta
# Link to existing project? [y/N] → N (primeira vez)
# What's your project's name? → mindloop-anp
# In which directory is your code located? → ./
# Want to override the settings? [y/N] → N
```

### Configurar Environment Variables

```bash
# Adicionar variáveis via CLI
vercel env add SERVERLESS_FAST_MODE production
# Valor: 1

vercel env add OPENAI_API_KEY production
# Valor: sk-proj-...

vercel env add OPENAI_CHAT_MODEL production
# Valor: gpt-4o-mini
```

### Re-deploy com Variáveis

```bash
vercel --prod
```

---

## ✅ Verificação Pós-Deploy

### 1. Verificar Logs

```bash
# Via CLI
vercel logs

# Via Dashboard
# https://vercel.com/your-username/mindloop-anp/deployments
```

### 2. Logs Esperados

```
======================================================================
 🚀 SERVERLESS MODE ATIVO
======================================================================
❌ FAISS DISABLED - Nenhum índice vetorial será carregado
❌ RAG BYPASS - Pipeline RAG completamente desabilitado
✅ LATS-P ATIVO - Todas as heurísticas, poda e entropia mantidas
✅ HITL ATIVO - Human-in-the-loop preservado
======================================================================
[SERVERLESS MODE] Memória episódica (FAISS) desabilitada
[CONFIG] Modo serverless - usando variáveis de ambiente
```

### 3. Testar Endpoints

```bash
# Health check
curl https://seu-app.vercel.app/
# Esperado: {"status": "ok"}

# Docs
# https://seu-app.vercel.app/docs

# Predict endpoint
curl -X POST https://seu-app.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "descricao_evento": "Vazamento de óleo no mar"
  }'
```

---

## 🔧 Troubleshooting

### Erro: "No module named 'numpy'"

**Causa**: requirements.txt contém numpy ou branch errado

**Solução**:
1. Verificar que está no branch `serverless_mvp`
2. Confirmar requirements.txt sem numpy
3. Re-deploy

### Erro: "Bundle size exceeds 250 MB"

**Causa**: Dependências pesadas ou arquivos não excluídos

**Solução**:
1. Verificar .vercelignore
2. Confirmar requirements.txt minimalista
3. Verificar que data/, notebooks/ estão excluídos

### Erro: "ModuleNotFoundError: langchain_community"

**Causa**: Código tentando importar módulo removido

**Solução**:
1. Verificar SERVERLESS_FAST_MODE=1 nas env vars
2. Confirmar que está no branch serverless_mvp

---

## 📊 Métricas Esperadas

| Métrica | Valor Esperado |
|---------|----------------|
| **Build time** | ~2-3 minutos |
| **Bundle size** | < 100 MB ✅ |
| **Cold start** | ~2-3 segundos |
| **Function size** | ~80-85 MB |
| **Deploy** | ✅ Sucesso |

---

## 🎯 Checklist Final

Antes de deploy, verificar:

- [ ] Branch correto (`serverless_mvp`)
- [ ] Código pushed para GitHub
- [ ] requirements.txt sem numpy, faiss-cpu
- [ ] vercel.json com SERVERLESS_FAST_MODE=1
- [ ] .vercelignore excluindo data/, notebooks/
- [ ] Variáveis de ambiente configuradas no Vercel

---

**Branch**: `serverless_mvp`
**Commit**: `1b4e113 - fix: Remover dependência de numpy`
**Status**: ✅ Pronto para deploy
