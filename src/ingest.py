import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from dotenv import load_dotenv
load_dotenv()

# Garantir que as variáveis de ambiente estão setadas
for k in ("OPENAI_API_KEY", "DATABASE_URL","PG_VECTOR_COLLECTION_NAME"):
    if not os.getenv(k):
        raise RuntimeError(f"Environment variable {k} is not set")

PDF_PATH = os.getenv("PDF_PATH")

def ingest_pdf():
    
    # Carregar o arquivo PDF
    docs = PyPDFLoader(str(PDF_PATH)).load()
    
    # Dividir o documento em chunks
    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150, 
        add_start_index=False).split_documents(docs)

    # Verificar se o documento foi dividido em chunks
    if not splits:
        raise SystemExit(0)

    # Criar documentos com metadados
    enriched = [
        # Criar documento com metadados
        Document(
            # Conteúdo do chunk
            page_content=d.page_content,
            # Metadados do chunk
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        # Iterar sobre os chunks
        for d in splits
    ]

    # Criar IDs para os documentos
    ids = [f"doc-{i}" for i in range(len(enriched))]

    # Criar embeddings para os documentos
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL","text-embedding-3-small"))

    # Criar store para os documentos
    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )

    # Adicionar documentos ao store
    store.add_documents(enriched, ids=ids)


if __name__ == "__main__":
    ingest_pdf()