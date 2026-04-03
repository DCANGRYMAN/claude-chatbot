from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import sqlite3
import json
import os

app = FastAPI(title="Assistente IA Pro", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "SUA_GROQ_API_KEY_AQUI")
client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("usuarios.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            nome TEXT,
            cargo_tipo TEXT,
            system_prompt TEXT,
            historico TEXT DEFAULT '[]',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────
# PERGUNTAS POR CARGO
# ─────────────────────────────────────────

PERGUNTAS_POR_CARGO = {
    "tecnologia": [
        {"id": "cargo", "pergunta": "Qual é o seu cargo atual?", "placeholder": "Ex: Dev Backend, Tech Lead, DevOps..."},
        {"id": "stack", "pergunta": "Quais linguagens e tecnologias você usa no dia a dia?", "placeholder": "Ex: Python, React, AWS, Docker..."},
        {"id": "responsabilidades", "pergunta": "Quais são suas principais responsabilidades semanais?", "placeholder": "Ex: code reviews, reuniões de sprint, deploys..."},
        {"id": "ferramentas", "pergunta": "Quais ferramentas de gestão e comunicação você usa?", "placeholder": "Ex: Jira, Slack, GitHub, Confluence..."},
        {"id": "dor", "pergunta": "Qual tarefa consome mais tempo e poderia ser automatizada?", "placeholder": "Ex: escrever tickets, documentar código, status reports..."},
    ],
    "administracao": [
        {"id": "cargo", "pergunta": "Qual é o seu cargo e área?", "placeholder": "Ex: Analista Financeiro, Coordenador de RH..."},
        {"id": "processos", "pergunta": "Quais processos você gerencia ou participa diariamente?", "placeholder": "Ex: conciliação bancária, folha de ponto, orçamentos..."},
        {"id": "ferramentas", "pergunta": "Quais ferramentas e sistemas você usa?", "placeholder": "Ex: Excel, SAP, Power BI, ERP Totvs..."},
        {"id": "equipe", "pergunta": "Você lidera ou interage com uma equipe? Quantas pessoas?", "placeholder": "Ex: Sim, equipe de 5 analistas..."},
        {"id": "dor", "pergunta": "Qual documento ou tarefa repetitiva mais consome seu tempo?", "placeholder": "Ex: relatórios semanais, atas de reunião, e-mails de status..."},
    ],
    "marketing": [
        {"id": "cargo", "pergunta": "Qual é o seu cargo em marketing?", "placeholder": "Ex: Analista de Conteúdo, Social Media, Growth..."},
        {"id": "canais", "pergunta": "Em quais canais você trabalha?", "placeholder": "Ex: Instagram, LinkedIn, e-mail marketing, blog..."},
        {"id": "ferramentas", "pergunta": "Quais ferramentas você usa no dia a dia?", "placeholder": "Ex: HubSpot, RD Station, Canva, Google Analytics..."},
        {"id": "publico", "pergunta": "Descreva o público-alvo da sua empresa", "placeholder": "Ex: PMEs do setor de saúde, decisores de TI..."},
        {"id": "dor", "pergunta": "Qual tipo de conteúdo ou copy você mais precisa criar?", "placeholder": "Ex: posts, e-mails de nutrição, relatórios de campanha..."},
    ],
    "geral": [
        {"id": "cargo", "pergunta": "Qual é o seu cargo e empresa?", "placeholder": "Ex: Analista na Empresa XYZ..."},
        {"id": "rotina", "pergunta": "Descreva sua rotina de trabalho típica", "placeholder": "Ex: reuniões pela manhã, análises à tarde..."},
        {"id": "ferramentas", "pergunta": "Quais ferramentas digitais você usa todo dia?", "placeholder": "Ex: Office, Google Workspace, Slack..."},
        {"id": "documentos", "pergunta": "Qual tipo de documento você mais produz?", "placeholder": "Ex: e-mails, relatórios, apresentações, planilhas..."},
        {"id": "dor", "pergunta": "O que você gostaria de automatizar ou agilizar primeiro?", "placeholder": "Ex: rascunho de e-mails, resumos de reuniões..."},
    ]
}

# ─────────────────────────────────────────
# CONSTRUTOR DE PERFIL
# ─────────────────────────────────────────

def construir_system_prompt(cargo_tipo: str, nome: str, respostas: dict) -> str:
    perguntas = PERGUNTAS_POR_CARGO.get(cargo_tipo, PERGUNTAS_POR_CARGO["geral"])

    contexto_linhas = []
    for p in perguntas:
        resp = respostas.get(p["id"], "não informado")
        contexto_linhas.append(f"- {p['pergunta']}: {resp}")
    contexto = "\n".join(contexto_linhas)

    prompt = f"""Você é o assistente de trabalho pessoal de {nome}, altamente especializado e contextualizado para o seu perfil profissional.

PERFIL DO USUÁRIO:
{contexto}

SUAS CAPACIDADES PRINCIPAIS:
1. Redigir e-mails profissionais completos e prontos para envio (com assunto e corpo)
2. Criar relatórios, atas, resumos e documentos profissionais
3. Responder dúvidas técnicas e administrativas do dia a dia
4. Sugerir melhorias de processo e automações relevantes ao cargo
5. Ajudar com apresentações, roteiros e comunicações internas
6. Adaptar toda resposta ao nível, tom e contexto profissional do usuário

REGRAS DE COMPORTAMENTO:
- Responda SEMPRE em português brasileiro, de forma direta e profissional
- Quando solicitado um documento (e-mail, relatório, ata), entregue o conteúdo COMPLETO e pronto para uso
- Use o perfil do usuário para personalizar cada resposta — nunca peça informações já declaradas
- Para e-mails: sempre forneça Assunto + Corpo completo
- Para relatórios: use estrutura clara com seções
- Seja conciso mas completo. Profissional mas humano.
- Se a tarefa for ambígua, faça UMA pergunta objetiva para clarificar antes de executar
"""
    return prompt

# ─────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────

class OnboardingData(BaseModel):
    user_id: str
    nome: str
    cargo_tipo: str
    respostas: dict

class ChatMessage(BaseModel):
    user_id: str
    mensagem: str

class ResetRequest(BaseModel):
    user_id: str

# ─────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────

@app.get("/perguntas/{cargo_tipo}")
def get_perguntas(cargo_tipo: str):
    perguntas = PERGUNTAS_POR_CARGO.get(cargo_tipo, PERGUNTAS_POR_CARGO["geral"])
    return {"cargo_tipo": cargo_tipo, "perguntas": perguntas}

@app.get("/cargos")
def get_cargos():
    return {
        "cargos": [
            {"id": "tecnologia", "label": "Tecnologia", "icon": "💻"},
            {"id": "administracao", "label": "Administração", "icon": "📊"},
            {"id": "marketing", "label": "Marketing", "icon": "📣"},
            {"id": "geral", "label": "Outro cargo", "icon": "🧑‍💼"},
        ]
    }

@app.post("/onboarding")
def salvar_onboarding(data: OnboardingData):
    system_prompt = construir_system_prompt(data.cargo_tipo, data.nome, data.respostas)
    conn = sqlite3.connect("usuarios.db")
    conn.execute(
        "INSERT OR REPLACE INTO usuarios (id, nome, cargo_tipo, system_prompt, historico) VALUES (?, ?, ?, ?, '[]')",
        (data.user_id, data.nome, data.cargo_tipo, system_prompt)
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "mensagem": f"Perfil de {data.nome} criado com sucesso!"}

@app.post("/chat")
def chat(msg: ChatMessage):
    conn = sqlite3.connect("usuarios.db")
    row = conn.execute(
        "SELECT nome, system_prompt, historico FROM usuarios WHERE id=?",
        (msg.user_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado. Complete o onboarding.")

    nome, system_prompt, historico_json = row
    historico = json.loads(historico_json)
    historico.append({"role": "user", "content": msg.mensagem})

    resposta = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "system", "content": system_prompt}] + historico[-20:],
        max_tokens=1500,
        temperature=0.7
    )

    texto = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": texto})

    conn = sqlite3.connect("usuarios.db")
    conn.execute(
        "UPDATE usuarios SET historico=? WHERE id=?",
        (json.dumps(historico), msg.user_id)
    )
    conn.commit()
    conn.close()

    return {"resposta": texto, "nome": nome}

@app.get("/perfil/{user_id}")
def ver_perfil(user_id: str):
    conn = sqlite3.connect("usuarios.db")
    row = conn.execute(
        "SELECT nome, cargo_tipo, system_prompt FROM usuarios WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"nome": row[0], "cargo_tipo": row[1], "system_prompt": row[2]}

@app.post("/reset")
def reset_historico(req: ResetRequest):
    conn = sqlite3.connect("usuarios.db")
    conn.execute("UPDATE usuarios SET historico='[]' WHERE id=?", (req.user_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "mensagem": "Histórico limpo com sucesso"}

@app.get("/")
def root():
    return {"status": "Assistente IA Pro rodando!", "docs": "/docs"}
