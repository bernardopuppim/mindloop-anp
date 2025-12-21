# ANP Classifier - Interface Next.js

Interface web moderna em Next.js para o sistema de classificação de eventos SMS.

## 🚀 Tecnologias

- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Componentes UI
- **Lucide React** - Ícones

## 📋 Pré-requisitos

- Node.js 18+ instalado
- Backend FastAPI rodando em `http://localhost:8000`

## 🛠️ Instalação

```bash
# Instalar dependências
npm install
```

## 🚀 Executar Localmente

### 1. Iniciar Backend (Terminal 1)

```bash
# Voltar para o diretório raiz do projeto
cd ..

# Ativar ambiente virtual
source .venv/bin/activate   # Linux/macOS
# ou
.venv\Scripts\activate      # Windows

# Iniciar FastAPI
uvicorn backend.main:app --reload
```

O backend estará rodando em `http://localhost:8000`

### 2. Iniciar Frontend (Terminal 2)

```bash
# No diretório ui-next
npm run dev
```

O frontend estará rodando em `http://localhost:3000`

### 3. Acessar Aplicação

Abra o navegador em: **http://localhost:3000**

## 📖 Como Usar

1. **Cole a descrição do evento** na caixa de texto
2. **Clique em "Classificar Evento"**
3. **Aguarde o resultado:**
   - Se o sistema tiver certeza, mostra a classe diretamente
   - Se houver incerteza (alta entropia), abre modal HITL
4. **No modal HITL:**
   - Revise as top-3 classes mais prováveis
   - Selecione a classe correta
   - O sistema continua a classificação

## 🎨 Interface

### Tela Principal
- ✅ Textarea para entrada do evento
- ✅ Botão "Classificar" com loading state
- ✅ Card de resultado com:
  - Classe final
  - Entropia
  - Justificativa

### Modal HITL
- ✅ Aparece quando `status === "hitl_required"`
- ✅ Mostra top-3 classes com scores
- ✅ Botões para seleção
- ✅ Primeira opção em destaque (mais provável)

## 🔌 Integração com API

### Endpoint 1: POST /predict

**Request:**
```json
{
  "texto_evento": "Durante atividade de manutenção..."
}
```

**Response (OK):**
```json
{
  "status": "ok",
  "classe": "Classe 2",
  "entropia": 0.23,
  "justificativa": "Lesão com tratamento médico..."
}
```

**Response (HITL Required):**
```json
{
  "status": "hitl_required",
  "top_classes": [
    {"classe": "Classe 2", "score": 0.42},
    {"classe": "Classe 3", "score": 0.38},
    {"classe": "Classe 4", "score": 0.20}
  ],
  "justificativa": "Incerteza detectada..."
}
```

### Endpoint 2: POST /hitl/continue

**Request:**
```json
{
  "classe_escolhida": "Classe 2"
}
```

**Response:**
```json
{
  "status": "ok",
  "classe": "Classe 2",
  "justificativa": "Classificação confirmada..."
}
```

## 📁 Estrutura de Arquivos

```
ui-next/
├── app/
│   ├── layout.tsx          # Layout raiz
│   ├── page.tsx            # Página principal (TODA A LÓGICA AQUI)
│   └── globals.css         # Estilos globais
├── components/
│   └── ui/
│       ├── button.tsx      # Componente Button
│       ├── card.tsx        # Componente Card
│       ├── dialog.tsx      # Componente Dialog (modal)
│       └── textarea.tsx    # Componente Textarea
├── lib/
│   └── utils.ts            # Utilitário cn() para classes
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🐛 Troubleshooting

### Erro: "Failed to fetch"

**Causa:** Backend não está rodando ou CORS bloqueado

**Solução:**
1. Verifique se o backend está em `http://localhost:8000`
2. Teste a API diretamente: `curl http://localhost:8000/docs`
3. Verifique CORS no backend (FastAPI já tem middleware configurado)

### Erro: "Port 3000 already in use"

**Solução:**
```bash
# Matar processo na porta 3000
npx kill-port 3000

# Ou rodar em outra porta
npm run dev -- -p 3001
```

### Modal HITL não abre

**Causa:** API retorna formato diferente do esperado

**Solução:**
1. Verifique a resposta da API no console do browser (F12)
2. Confirme que `status === "hitl_required"` está vindo corretamente

## 🔄 Workflow Completo

```
Usuário cola evento
    ↓
Clica "Classificar"
    ↓
Loading state ativa
    ↓
POST /predict
    ↓
┌─────────────────┬─────────────────┐
│  status: "ok"   │ status: "hitl"  │
├─────────────────┼─────────────────┤
│ Mostra resultado│ Abre modal HITL │
│ em card verde   │ com top-3       │
└─────────────────┤                 │
                  │ Usuário seleciona
                  │       ↓
                  │ POST /hitl/continue
                  │       ↓
                  │ Mostra resultado
                  └─────────────────
```

## 🎯 Próximos Passos (Fora do Escopo Atual)

- [ ] Histórico de classificações
- [ ] Exportação de resultados
- [ ] Autenticação
- [ ] Dashboard de métricas
- [ ] Deploy no Vercel

## 📝 Notas Técnicas

- **Estado gerenciado com React hooks** (useState)
- **Fetch API nativo** (sem Axios)
- **URL hardcoded** em `API_URL` (sem variáveis de ambiente por enquanto)
- **Componentes shadcn/ui** copiados manualmente (não via CLI)
- **Sem SSR** - página é 100% client-side ("use client")

---

**Desenvolvido para validação local. Não é produção.**
