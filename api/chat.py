from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI(title="Assistente IA Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is obrigatório no ambiente")

client = Groq(api_key=GROQ_API_KEY)

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
    ],
}


def construir_system_prompt(cargo_tipo: str, nome: str, respostas: dict) -> str:
    perguntas = PERGUNTAS_POR_CARGO.get(cargo_tipo, PERGUNTAS_POR_CARGO["geral"])
    contexto_linhas = []
    for pergunta in perguntas:
        valor = respostas.get(pergunta["id"], "não informado")
        contexto_linhas.append(f"- {pergunta['pergunta']}: {valor}")
    contexto = "\n".join(contexto_linhas)
    return f"""Você é o assistente de trabalho pessoal de {nome}, altamente especializado e contextualizado para o seu perfil profissional.

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


class ChatRequest(BaseModel):
    nome: str
    cargo_tipo: str
    respostas: dict
    historico: list[dict]


@app.post("/")
def chat(request: ChatRequest):
    system_prompt = construir_system_prompt(request.cargo_tipo, request.nome, request.respostas)
    messages = [{"role": "system", "content": system_prompt}] + request.historico
    try:
        resposta = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages[-20:],
            max_tokens=1500,
            temperature=0.7,
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

    texto = getattr(resposta.choices[0].message, 'content', None)
    if texto is None:
        raise HTTPException(status_code=500, detail="Resposta inválida do modelo")
    return {"resposta": texto}
