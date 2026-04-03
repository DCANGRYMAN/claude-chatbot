# ✦ Assistente IA Pro

Seu assistente de trabalho pessoal, treinado com seu perfil profissional.
Powered by **Llama 3 70B** via Groq API (100% gratuito).

---

## 🚀 Como rodar em 5 minutos

### 1. Obtenha sua API Key gratuita do Groq
- Acesse: https://console.groq.com
- Crie uma conta e gere uma API Key
- É gratuito, sem cartão de crédito

### 2. Configure o backend

```bash
cd backend

# Instale as dependências
pip install -r requirements.txt

# Crie o arquivo .env
cp .env.example .env

# Abra o .env e cole sua chave do Groq:
# GROQ_API_KEY=gsk_sua_chave_aqui
```

### 3. Rode o backend

```bash
cd backend
uvicorn app:app --reload
```

O servidor vai rodar em: http://localhost:8000
Documentação da API: http://localhost:8000/docs

### 4. Abra o frontend

Abra o arquivo `frontend/index.html` diretamente no navegador.
Ou sirva com um servidor local:

```bash
cd frontend
python -m http.server 3000
# Acesse: http://localhost:3000
```

---

## 📁 Estrutura do projeto

```
assistente-ia/
├── api/
│   └── chat.py             # Função serverless Vercel (stateless)
├── backend/
│   ├── app.py              # API principal (FastAPI)
│   ├── requirements.txt    # Dependências Python
│   └── .env.example        # Modelo do arquivo de configuração
├── frontend/
│   ├── index.html          # Onboarding (configuração do perfil)
│   └── chat.html           # Interface do assistente
├── requirements.txt        # Dependências Python para Vercel
├── vercel.json             # Rewrites para servir frontend e API juntos
└── README.md
```

---

## 🛠️ Como funciona

1. **Onboarding**: O usuário responde 5 perguntas sobre seu cargo e rotina
2. **Perfil dinâmico**: As respostas constroem um `system prompt` personalizado
3. **Assistente contextualizado**: O Llama 3 age com base no perfil do usuário
4. **Tarefas automatizadas**: Redige e-mails, relatórios, atas e documentos completos

---

## ✏️ Como personalizar

### Adicionar novos cargos
Em `backend/app.py`, adicione um novo bloco em `PERGUNTAS_POR_CARGO`:

```python
"juridico": [
    {"id": "cargo", "pergunta": "Qual é sua especialidade jurídica?", "placeholder": "Ex: Direito Trabalhista, Contratos..."},
    # ... mais perguntas
]
```

E no frontend (`index.html`), adicione o novo cargo no grid:
```html
<div class="cargo-card" onclick="selecionarCargo('juridico', this)">
  <div class="cargo-icon">⚖️</div>
  <div class="cargo-label">Jurídico</div>
</div>
```

### Adicionar ações rápidas no chat
Em `chat.html`, adicione botões na sidebar:

```html
<button class="qa-btn" onclick="atalho('Sua instrução aqui')">
  <span class="qa-icon">🎯</span> Nome da ação
</button>
```

### Trocar o modelo LLM
Em `backend/app.py`, linha do `client.chat.completions.create`:
- `llama3-70b-8192` → mais inteligente (padrão)
- `llama3-8b-8192` → mais rápido e leve
- `mixtral-8x7b-32768` → contexto maior (32k tokens)

---

## ☁️ Deploy gratuito

### Backend (Render.com)
1. Crie conta em https://render.com
2. Conecte seu repositório GitHub
3. Novo serviço → Web Service → selecione a pasta `backend`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. Adicione a variável de ambiente: `GROQ_API_KEY=sua_chave`

### Frontend (Vercel ou Netlify)
1. Faça upload da pasta `frontend`
2. Atualize a variável `API` nos arquivos HTML para a URL do seu backend no Render

---

## 🗺️ Roadmap sugerido

- [ ] Login com Google (Firebase Auth — gratuito)
- [ ] Upload de PDF do catálogo/documentos internos (RAG)
- [ ] Histórico persistente por usuário no banco
- [ ] Templates salvos de e-mails e relatórios
- [ ] Plano free (X mensagens/dia) + monetização

---

## 💡 Custos

| Serviço | Plano | Custo |
|---------|-------|-------|
| Groq API (Llama 3) | Free tier | R$ 0 |
| Render.com | Free tier | R$ 0 |
| Netlify/Vercel | Free tier | R$ 0 |
| **Total** | | **R$ 0** |
# claude-chatbot
