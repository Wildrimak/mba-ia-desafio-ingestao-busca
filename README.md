# Desafio MBA — Ingestão e Busca Semântica com LangChain e Postgres (pgVector)

Software que ingere um PDF em um banco vetorial (Postgres + pgVector) e permite fazer perguntas sobre o conteúdo desse PDF via linha de comando, usando RAG (Retrieval-Augmented Generation) com LangChain. As respostas ficam restritas ao que está no documento — perguntas fora do contexto são recusadas explicitamente.

## Pré-requisitos

- Python 3.10+
- Docker e Docker Compose
- Uma API Key da OpenAI ([platform.openai.com](https://platform.openai.com))

## 1. Ambiente virtual

PowerShell (Windows):

```powershell
python3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Configurar variáveis de ambiente

Copie o template e preencha:

```powershell
copy .env.example .env
```

Edite o `.env`:

| Variável | Descrição | Exemplo |
|---|---|---|
| `OPENAI_API_KEY` | Sua chave da API da OpenAI | `sk-...` |
| `OPENAI_EMBEDDING_MODEL` | Modelo de embeddings | `text-embedding-3-small` |
| `DATABASE_URL` | String de conexão com o Postgres | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` |
| `PG_VECTOR_COLLECTION_NAME` | Nome da coleção dentro do pgVector | `pdf_documents` |
| `PDF_PATH` | Caminho do PDF a ser ingerido | `document.pdf` |

As variáveis `GOOGLE_API_KEY` / `GOOGLE_EMBEDDING_MODEL` não são usadas nesta versão (o projeto usa OpenAI) — podem ficar em branco.

## 3. Subir o banco de dados

```powershell
docker compose up -d
```

Sobe um Postgres com a extensão `pgvector` habilitada, na porta `5432`.

## 4. Ingerir o PDF

```powershell
python src/ingest.py
```

Lê o `document.pdf`, divide o texto em chunks de 1000 caracteres (com 150 de sobreposição), gera um embedding para cada chunk e grava tudo no Postgres.

## 5. Rodar o chat

```powershell
python src/chat.py
```

Exemplo de uso:

```
Faça sua pergunta: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de R$ 10.000.000,00.

Faça sua pergunta: Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

Digite `sair` para encerrar.

## Como funciona

1. **Ingestão** (`src/ingest.py`): o PDF é carregado (`PyPDFLoader`), dividido em pedaços de texto (`RecursiveCharacterTextSplitter`) e cada pedaço vira um vetor numérico (embedding) via API da OpenAI. Texto e vetor são salvos no Postgres através do `PGVector` (LangChain), que cria automaticamente as tabelas necessárias.
2. **Busca** (`src/search.py`): a pergunta do usuário é comparada, por similaridade vetorial (dentro do próprio Postgres), contra os vetores salvos, retornando os 10 chunks mais parecidos (`k=10`). Esses chunks viram o `CONTEXTO` de um prompt fixo, que instrui a LLM a responder **somente** com base nesse contexto, nunca com conhecimento externo.
3. **Chat** (`src/chat.py`): loop de terminal que recebe a pergunta, chama a busca e imprime a resposta.

## Limitações conhecidas

Busca por similaridade vetorial encontra texto **semanticamente parecido**, não faz correspondência exata de palavra (não é um `Ctrl+F`). Isso funciona muito bem para perguntas pontuais ("qual o faturamento da empresa X?"), mas pode falhar em:

- **Perguntas de agregação** ("qual empresa tem o maior faturamento?") — a busca traz apenas uma amostra (`k=10`) do documento, não o dado inteiro, então não há garantia de que o valor máximo real esteja entre os chunks retornados.
- **Busca por palavra-chave isolada** ("quais empresas têm 'X' no nome?") — se o dado relevante estiver "diluído" dentro de um chunk com muitos outros assuntos, ele pode não ser recuperado, mesmo existindo no documento. Uma solução mais robusta combinaria busca vetorial com busca textual tradicional (`ILIKE` / full-text search) no Postgres.

## Estrutura do projeto

```
├── docker-compose.yml    # Postgres + pgVector
├── requirements.txt      # Dependências Python
├── .env.example          # Template de variáveis de ambiente
├── src/
│   ├── ingest.py          # Ingestão do PDF
│   ├── search.py          # Busca + montagem do prompt + chamada à LLM
│   ├── chat.py            # CLI de chat
├── document.pdf           # PDF usado na ingestão
└── README.md
```
