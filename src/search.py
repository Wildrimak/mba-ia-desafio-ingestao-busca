import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def search_prompt(question=None):
    
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL","text-embedding-3-small"))
    
    # Criar store para os documentos
    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )

    # Vetorizando a pergunta e fazendo a busca com 10 resultados
    results = store.similarity_search_with_score(question, k=10)

    # Concatenando os chunks em uma String
    contexto = ""
    for result in results:
        chunk = result[0].page_content
        contexto += chunk + "\n\n--\n\n"

    query = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)

    chat = ChatOpenAI(model="gpt-5-nano", temperature=0.1)
    resultado = chat.invoke(query)
    resposta = resultado.content
    
    return resposta