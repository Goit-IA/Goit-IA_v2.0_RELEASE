# --- modelo_llm.py ---
import os
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- CONFIGURACIÓN ---
CHROMA_PATH = "chroma_db_web"
MODELO_EMBEDDING = "nomic-embed-text"
MODELO_GROQ = "llama-3.3-70b-versatile"
GROQ_API_KEY = "" # Tu Key

def obtener_cadena_rag():
    # 1. Verificación de seguridad
    if not os.path.exists(CHROMA_PATH):
        return None # Indica que la BD no existe

    # 2. Cargar la BD desde el disco
    embedding_function = OllamaEmbeddings(model=MODELO_EMBEDDING)
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # 3. Configurar el recuperador (Top 5 resultados más relevantes)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 4. Prompt optimizado para RAG
    template = """
    Eres un asistente experto de la Universidad Veracruzana.
    Responde a la pregunta basándote ÚNICAMENTE en el contexto proporcionado abajo.
    Si la respuesta no está en el contexto, di "No tengo esa información".
    
    CONTEXTO RECUPERADO:
    {context}
    
    PREGUNTA DEL USUARIO:
    {question}
    
    RESPUESTA (Sé claro, usa viñetas si es necesario):
    """
    prompt = ChatPromptTemplate.from_template(template)

    # 5. Configurar el LLM (Groq)
    llm = ChatGroq(
        model=MODELO_GROQ,
        api_key=GROQ_API_KEY,
        temperature=0.2 # Baja temperatura para ser más preciso
    )

    # 6. Crear la cadena
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain