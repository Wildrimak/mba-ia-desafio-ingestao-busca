import os
from search import search_prompt

# Garantir que as variáveis de ambiente estão setadas
for k in ("OPENAI_API_KEY", "DATABASE_URL","PG_VECTOR_COLLECTION_NAME"):
    if not os.getenv(k):
        raise RuntimeError(f"Environment variable {k} is not set")

def main():
    while True:
        
        pergunta = input("Faça sua pergunta: ")
        
        if pergunta.lower() == "sair":
            break

        print("PERGUNTA: ", pergunta)
        print(f"RESPOSTA: {search_prompt(pergunta)}")

if __name__ == "__main__":
    main()