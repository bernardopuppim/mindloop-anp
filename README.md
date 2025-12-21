# ANP Classifier - Sistema de Classificação de Eventos SMS

Sistema inteligente de classificação de eventos de Segurança, Meio Ambiente e Saúde (SMS) para a Petrobras/ANP, baseado em **LATS-P** (Language Agent Tree Search with Pruning) + **RAG** (Retrieval-Augmented Generation) + **HITL** (Human-in-the-Loop).

---

## 📋 Funcionalidades

- **RAG Híbrido**: Busca semântica (FAISS) + BM25 + Reranking
- **LATS-P**: Navegação inteligente em árvore de decisão com poda probabilística
- **HITL**: Intervenção humana quando há incerteza (alta entropia)
- **Memória Episódica**: Reutilização de decisões humanas passadas (SQLite + FAISS)
- **Sistema de Evolução Offline**: Análise e melhoria automática da árvore de decisão
- **Interface Web**: Next.js UI + FastAPI Backend

---

## 🛠️ Instalação

### 1. Pré-requisitos

- Python 3.10+
- Node.js 18+ (para frontend Next.js)
- Chave API OpenAI

### 2. Clone e Ambiente Virtual

```bash
git clone <repo-url>
cd ANP_classifier

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar OpenAI

#### Obter Chave API

1. Acesse: https://platform.openai.com/api-keys
2. Crie uma nova chave API
3. Copie a chave (começa com `sk-proj-...`)

#### Configurar Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite `.env` e adicione sua chave:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
```

#### Custos Estimados (OpenAI)

| Operação | Custo por evento | Custo 1000 eventos |
|----------|------------------|-------------------|
| Classificação normal | $0.002 - $0.005 | $2 - $5 |
| FAST_MODE=1 | $0.001 - $0.003 | $1 - $3 |

**Modelos usados:**
- **gpt-4o-mini**: $0.15/1M tokens entrada, $0.60/1M saída
- **text-embedding-3-small**: $0.02/1M tokens

---

## 🚀 Uso

### Backend (FastAPI)

```bash
# Ativar venv
source .venv/bin/activate

# Iniciar servidor
uvicorn backend.main:app --reload

# Servidor rodando em: http://localhost:8000
```

### Frontend (Next.js)

```bash
# Em outro terminal
cd ui-next

# Instalar dependências (primeira vez)
npm install

# Iniciar dev server
npm run dev

# Interface disponível em: http://localhost:3000
```

### API Endpoints

#### POST /predict
Classifica um evento:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"texto_evento": "Vazamento de óleo na plataforma P-50"}'
```

**Resposta (sem HITL):**
```json
{
  "hitl_required": false,
  "final": {
    "node_id": "1.2.3.1",
    "log_prob": -2.45,
    "historico": [...]
  },
  "state": {...}
}
```

**Resposta (com HITL):**
```json
{
  "hitl_required": true,
  "hitl_metadata": {
    "node_id": "1.2",
    "pergunta": "O evento envolve poluição?",
    "entropia_local": 1.45,
    "children": [
      {"id": "1.2.1", "score": 0.45, "prob": 0.33, ...},
      {"id": "1.2.2", "score": 0.42, "prob": 0.31, ...}
    ]
  },
  "state": {...}
}
```

#### POST /hitl/continue
Continua classificação após decisão humana:

```bash
curl -X POST http://localhost:8000/hitl/continue \
  -H "Content-Type: application/json" \
  -d '{
    "state": {...},
    "selected_child": "1.2.1",
    "justification": "Evento claramente relacionado a poluição marinha"
  }'
```

---

## ⚡ FAST_MODE

Ativa otimizações de performance (contexto RAG reduzido, menos tokens):

```bash
# Em .env
FAST_MODE=1
```

**Características:**
- ✅ ~30% mais rápido
- ✅ ~30% mais barato
- ✅ HITL continua funcionando normalmente
- ⚠️ Pode ter leve redução de precisão em casos muito complexos

---

## 🧪 Testes

### Teste Rápido Backend

```bash
# Classificação simples
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"texto_evento": "Acidente com empilhadeira"}'
```

### Teste Frontend

1. Abra http://localhost:3000
2. Cole: "Vazamento de produto químico durante transferência"
3. Clique "Classificar Evento"
4. Se HITL aparecer: escolha uma opção e justifique
5. Veja resultado final

---

## 📁 Estrutura do Projeto

```
ANP_classifier/
├── backend/               # FastAPI backend
│   ├── main.py           # Rotas API
│   ├── models.py         # Schemas Pydantic
│   └── services/         # Lógica de negócio
├── lats_sistema/         # Core LATS-P + RAG
│   ├── lats/            # Engine LATS-P
│   ├── rag/             # Pipeline RAG
│   ├── graph/           # Grafo LangGraph
│   ├── models/          # LLM/Embeddings factory
│   └── memory/          # Memória episódica
├── ui-next/             # Frontend Next.js
│   ├── app/             # Pages
│   └── components/      # UI components
└── data/                # Árvore de decisão + corpus
```

---

## 🔧 Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"

```bash
# Verifique se .env existe
cat .env | grep OPENAI_API_KEY

# Se não existir, copie do exemplo
cp .env.example .env
# E edite adicionando sua chave
```

### Erro: "Failed to fetch" no frontend

```bash
# Verifique se backend está rodando
curl http://localhost:8000/docs

# Verifique CORS no backend (já configurado)
```

### HITL não aparece

Verifique logs do backend - se a entropia for sempre baixa, o modelo está muito confiante. Eventos ambíguos acionam HITL automaticamente.

---

## 📚 Documentação Adicional

- `HITL_ARCHITECTURE_FINAL.md` - Arquitetura HITL detalhada
- `FAST_MODE_README.md` - Detalhes do modo rápido
- `.env.example` - Todas as variáveis disponíveis

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📄 Licença

Este projeto é propriedade da Petrobras/ANP.

---

## 🆘 Suporte

Para questões ou problemas, abra uma issue no repositório.
