# 📓 Notebooks - ANP Classifier

## 📋 Visão Geral

Este diretório contém Jupyter Notebooks para processamento de documentos normativos da ANP e geração de artefatos para o classificador LATS-P.

---

## 📚 Notebooks Disponíveis

### 1. `ANP_pdf_to_KG_policy_tree.ipynb` ⭐ PRINCIPAL

**Objetivo**: Pipeline completo de extração de PDFs normativos da ANP até geração de árvore de decisão JSON.

**Fluxo**:
```
PDFs Normativos
    ↓
[0] Setup e Imports
    ↓
[1] Descoberta de PDFs
    ↓
[2] Extração de Texto (PyMuPDF + OCR fallback)
    ↓
[3] Limpeza e Normalização
    ↓
[4] Chunking (por seções ou tamanho)
    ↓
[5] Configuração LLM (Azure OpenAI)
    ↓
[6] Knowledge Graph (LLMGraphTransformer)
    ↓
[7] Policy Graph (projeção decisória)
    ↓
[7.5] Detecção Automática de Subpolicies ✨ NOVO
    ↓
[8] Compilação em Árvore JSON (com branching por subpolicies)
    ↓
[9] Relatório de Qualidade
    ↓
[10] Smoke Test
    ↓
Artefatos Finais (artifacts/)
```

**Outputs**:
- `artifacts/anp_text_corpus.jsonl` - Textos limpos
- `artifacts/anp_kg.graphml` - Knowledge Graph completo
- `artifacts/anp_kg.json` - Knowledge Graph (JSON)
- `artifacts/anp_policy.graphml` - Policy Graph (DAG)
- `artifacts/anp_policy.json` - Policy Graph (JSON)
- `artifacts/anp_tree.json` - Árvore de decisão final ✨

---

## 🚀 Como Usar

### Pré-requisitos

1. **Python 3.10+** com Jupyter instalado
2. **Azure OpenAI** configurado (credenciais no `.env`)
3. **Tesseract OCR** instalado (opcional, para PDFs com imagens)

### Instalação de Dependências

```bash
# Criar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install pymupdf pdfplumber pytesseract pillow langchain langchain-experimental langchain-openai networkx pydantic python-dotenv tqdm matplotlib jupyter
```

### Instalação do Tesseract (opcional)

**Ubuntu/Debian**:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

**macOS**:
```bash
brew install tesseract tesseract-lang
```

**Windows**:
Download do instalador: https://github.com/UB-Mannheim/tesseract/wiki

### Preparar PDFs

Coloque os PDFs normativos da ANP em:
```
padroes_anp/
├── portaria_anp_XXX.pdf
├── resolucao_anp_YYY.pdf
└── ...
```

### Configurar Azure OpenAI

Crie arquivo `.env` na raiz do projeto:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://seu-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=sua-chave-api
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### Executar Notebook

```bash
# Iniciar Jupyter
jupyter notebook notebooks/ANP_pdf_to_KG_policy_tree.ipynb

# Ou usar JupyterLab
jupyter lab notebooks/ANP_pdf_to_KG_policy_tree.ipynb
```

### Modo de Teste vs Produção

Por padrão, o notebook está em **MODO DE TESTE** (processa apenas 10 chunks):

```python
TEST_MODE = True  # Processar apenas 10 chunks
MAX_CHUNKS_TEST = 10
```

Para processar **corpus completo** (⚠️ pode custar muito em tokens):

```python
TEST_MODE = False  # Processar todos os chunks
```

---

## 📊 Estrutura dos Artefatos

### 1. `anp_text_corpus.jsonl`

Corpus de textos limpos, um documento por linha:

```json
{
  "doc_id": "a1b2c3d4e5f6",
  "filename": "portaria_anp_123.pdf",
  "text_clean": "Texto normalizado e limpo...",
  "num_chars": 45678,
  "num_words": 7890
}
```

### 2. `anp_kg.graphml` / `anp_kg.json`

Knowledge Graph completo com entidades normativas:

**Tipos de Nós**:
- `IncidentType` - Tipos de incidente
- `Criterion` - Critérios decisórios
- `Threshold` - Limiares numéricos
- `Classification` - Classificações (Classe 1, 2, etc)
- `Obligation` - Obrigações normativas
- `Exception` - Exceções
- `Actor` - Atores envolvidos
- `Evidence` - Evidências necessárias

**Tipos de Relações**:
- `DEPENDS_ON` - Dependência entre critérios
- `CLASSIFIED_AS` - Leva à classificação
- `IMPLIES` - Implica consequência
- `REQUIRES` - Requer evidência/ação
- `HAS_THRESHOLD` - Possui limiar
- `HAS_EXCEPTION` - Possui exceção
- `APPLIES_TO` - Aplica-se a
- `EVIDENCED_BY` - Evidenciado por

### 3. `anp_policy.graphml` / `anp_policy.json`

Policy Graph (projeção decisória do KG):

- Subgrafo do KG focado em decisão
- Apenas nós/arestas relevantes para classificação
- Validado como DAG (sem ciclos)

### 4. `anp_tree.json` ✨ PRINCIPAL

Árvore de decisão final, compatível com classificador LATS-P:

```json
{
  "id": "raiz",
  "pergunta": "Qual o tipo de ocorrência?",
  "tipo": "decisao",
  "subnodos": [
    {
      "id": "lesao_forca_trabalho",
      "pergunta": "Acidente com Lesão na Força de Trabalho",
      "tipo": "decisao",
      "subnodos": [
        {
          "id": "criterio_gravidade",
          "pergunta": "Qual a gravidade da lesão?",
          "tipo": "decisao",
          "subnodos": [
            {
              "id": "classe_1_terminal",
              "tipo": "terminal",
              "classe": "Classe 1"
            }
          ]
        }
      ]
    }
  ]
}
```

**Estrutura**:
- **Nós de Decisão**: `tipo: "decisao"` com `pergunta` e `subnodos`
- **Nós Terminais**: `tipo: "terminal"` com `classe`

---

## ✨ Detecção Automática de Subpolicies (NOVO)

**Seção [7.5]**: Implementa detecção automática de comunidades (subpolicies) usando teoria de grafos.

### Fundamento Teórico

**Detecção de Comunidades**:
- Algoritmo: `greedy_modularity_communities` (NetworkX)
- Princípio: Otimização de modularidade
- Resultado: Clusters naturais de nós = subpolicies (domínios normativos)

**Identificação de Nós Críticos**:
- Métrica: Betweenness centrality
- Significado: Nós que conectam diferentes partes do grafo (pontes estruturais)
- Uso: Auditoria de critérios decisórios mais importantes

### Vantagens

✅ **Eliminação de heurísticas manuais** - Baseado exclusivamente na topologia do grafo
✅ **Redução de entropia** - Branching inicial por domínio normativo
✅ **Maior granularidade** - Aumento de nós terminais
✅ **Determinístico** - Mesmos inputs → mesmos outputs
✅ **Auditável** - Cada decisão tem fundamentação estrutural

### Estrutura da Árvore com Subpolicies

```json
{
  "id": "raiz",
  "pergunta": "Qual o tipo de ocorrência?",
  "tipo": "decisao",
  "subnodos": [
    {
      "id": "subpolicy_0",
      "pergunta": "Acidente com Lesão na Força de Trabalho",
      "tipo": "decisao",
      "subnodos": [ /* critérios específicos */ ]
    },
    {
      "id": "subpolicy_1",
      "pergunta": "Acidente com Impacto no Meio Ambiente",
      "tipo": "decisao",
      "subnodos": [ /* critérios específicos */ ]
    }
  ]
}
```

**Resultado**: Árvore hierárquica com ramificação semântica, reduzindo entropia e melhorando navegação LATS-P.

**Documentação Completa**: Ver [CHANGELOG_SUBPOLICIES_DETECTION.md](CHANGELOG_SUBPOLICIES_DETECTION.md)

---

## ⚙️ Customização

### Ajustar Schema do KG

Editar listas `ALLOWED_NODES` e `ALLOWED_RELATIONSHIPS` na célula [6]:

```python
ALLOWED_NODES = [
    "IncidentType",
    "Criterion",
    # ... adicionar novos tipos
]

ALLOWED_RELATIONSHIPS = [
    "DEPENDS_ON",
    "CLASSIFIED_AS",
    # ... adicionar novas relações
]
```

### Ajustar Prompt Guia

Modificar `DECISIONAL_GUIDE` na célula [6] para direcionar extração:

```python
DECISIONAL_GUIDE = """
Extraia apenas conceitos para CLASSIFICAR INCIDENTES.

FOQUE EM:
- Critérios perguntáveis
- Thresholds numéricos
- ...
"""
```

### Ajustar Chunking

Modificar função `chunk_por_secoes()` na célula [4]:

```python
def chunk_por_secoes(doc: Dict[str, Any], max_chunk_chars: int = 6000):
    # Ajustar max_chunk_chars para chunks maiores/menores
    ...
```

---

## 🐛 Troubleshooting

### Erro: "Nenhum PDF encontrado"

**Causa**: Diretório `padroes_anp/` vazio

**Solução**: Copiar PDFs para `padroes_anp/`

### Erro: "pytesseract não disponível"

**Causa**: Tesseract OCR não instalado

**Solução**:
- Instalar Tesseract (ver seção "Instalação do Tesseract")
- OU desabilitar OCR (não afeta extração de PDFs com texto)

### Erro: "AZURE_OPENAI_ENDPOINT não configurado"

**Causa**: Arquivo `.env` faltando ou incompleto

**Solução**: Criar `.env` com credenciais Azure OpenAI

### Aviso: "Grafo contém ciclos"

**Causa**: KG gerado possui ciclos (normal em grafos de conhecimento)

**Solução**: O notebook remove ciclos automaticamente na célula [7]

### Performance: Notebook muito lento

**Causas possíveis**:
1. Muitos chunks sendo processados
2. Modelo LLM lento
3. Chunks muito grandes

**Soluções**:
1. Usar `TEST_MODE = True` para testes iniciais
2. Reduzir `MAX_CHUNKS_TEST`
3. Ajustar `max_chunk_chars` para chunks menores

---

## 💰 Estimativa de Custos (Azure OpenAI)

### Modo de Teste (10 chunks)

- **Tokens estimados**: ~50k tokens
- **Custo estimado**: ~$0.05 USD (com gpt-4o-mini)

### Modo Produção (corpus completo)

Depende do número de PDFs e tamanho:

| PDFs | Chunks | Tokens Estimados | Custo (gpt-4o-mini) |
|------|--------|------------------|---------------------|
| 5    | ~100   | ~500k            | ~$0.50 USD          |
| 10   | ~200   | ~1M              | ~$1.00 USD          |
| 20   | ~400   | ~2M              | ~$2.00 USD          |

⚠️ **Custos são estimativas**. Monitorar uso real no Azure Portal.

---

## 📈 Métricas de Qualidade

### Boas Métricas

- **Coverage**: > 80% dos nós Policy são Criterion ou Classification
- **DAG válido**: Policy Graph sem ciclos
- **Profundidade árvore**: 3-6 níveis (nem muito rasa, nem muito profunda)
- **Classes terminais**: > 5 classes diferentes
- **Conectividade KG**: Densidade entre 0.01-0.10

### Métricas Ruins

- ❌ KG com < 10 nós (extração falhou)
- ❌ Policy Graph com ciclos não resolvidos
- ❌ Árvore com profundidade 1 (muito rasa)
- ❌ Todas as folhas com mesma classe (não discriminativo)

---

## 🔄 Reexecução e Iteração

O notebook é **idempotente** - pode ser reexecutado sem problemas:

1. **Reprocessar PDFs novos**: Adicionar PDFs e reexecutar células [1]-[3]
2. **Ajustar KG**: Modificar schema/prompt e reexecutar célula [6]
3. **Refinar Policy**: Ajustar projeção e reexecutar célula [7]
4. **Recompilar árvore**: Ajustar compilação e reexecutar célula [8]

**Artefatos anteriores são sobrescritos** - fazer backup se necessário.

---

## 📚 Próximos Passos

### Validação e Refinamento

1. **Revisão Manual**: Abrir `anp_tree.json` e validar coerência normativa
2. **Teste com Eventos Reais**: Usar árvore no classificador LATS-P
3. **Ajuste de Prompts**: Refinar `DECISIONAL_GUIDE` baseado em resultados
4. **Expansão de Schema**: Adicionar novos tipos de nós/relações se necessário

### Integração com LATS-P

```python
# Em lats_sistema/lats/tree_loader.py
with open("artifacts/anp_tree.json", "r") as f:
    TREE_DATA = json.load(f)

# Usar TREE_DATA no lugar de árvore hardcoded
```

### Melhoria Contínua

1. **Chunking Semântico**: Usar embeddings para chunks mais inteligentes
2. **Validação por LLM**: Adicionar etapa de validação automática da árvore
3. **Versionamento**: Versionar artefatos (v1, v2, etc)
4. **Métricas Automáticas**: Adicionar testes de qualidade automáticos

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Verificar logs de execução no notebook
2. Consultar documentação LangChain: https://python.langchain.com/docs/
3. Revisar documentação NetworkX: https://networkx.org/documentation/

---

**Última atualização**: 2025-12-20
**Versão**: 1.0
