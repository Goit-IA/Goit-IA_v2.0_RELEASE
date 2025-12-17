import os
import shutil
import time
import gc
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# --- CONFIGURACIÓN ---
CHROMA_PATH = "data/chroma_db_web"
MODELO_EMBEDDING = "nomic-embed-text"

def actualizar_base_datos_completa(registry_data):
    """
    Recibe el diccionario del registry.json con 'urls' y 'pdfs'.
    Estrategia: Cargar documentos -> Conectar a DB -> Borrar datos viejos -> Insertar nuevos.
    """
    print("🚀 Iniciando proceso de entrenamiento con PDFs y URLs...")
    
    # 1. Preparar Documentos para RAG (URLs + PDFs)
    todos_los_documentos = []
    
    # A) Procesar URLs
    urls = [item['url'] for item in registry_data.get('urls', [])]
    if urls:
        print(f"📡 Descargando {len(urls)} URLs...")
        try:
            loader_web = WebBaseLoader(urls)
            docs_web = loader_web.load()
            todos_los_documentos.extend(docs_web)
        except Exception as e:
            print(f"⚠️ Error cargando URLs: {e}")

    # B) Procesar PDFs
    pdfs = registry_data.get('pdfs', [])
    for pdf_item in pdfs:
        path = pdf_item.get('path')
        if os.path.exists(path):
            print(f"📄 Procesando PDF: {pdf_item['filename']}")
            try:
                loader_pdf = PyPDFLoader(path)
                docs_pdf = loader_pdf.load()
                todos_los_documentos.extend(docs_pdf)
            except Exception as e:
                print(f"⚠️ Error leyendo PDF {path}: {e}")
        else:
            print(f"⚠️ Archivo no encontrado: {path}")

    # 2. Actualizar ChromaDB (Sin borrar la carpeta)
    if todos_los_documentos:
        print("🔪 Dividiendo texto en fragmentos...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(todos_los_documentos)
        print(f"📊 Se generaron {len(chunks)} fragmentos de texto.")

        print("🔄 Actualizando base de datos vectorial...")
        
        # Inicializamos el modelo de embeddings
        embedding_function = OllamaEmbeddings(model=MODELO_EMBEDDING)
        
        # Conectamos a la DB existente (o se crea si no existe)
        vector_db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embedding_function
        )
        
        # PASO CLAVE: Borrar contenido previo sin borrar carpeta
        try:
            # Obtenemos todos los IDs actuales en la base de datos
            existing_ids = vector_db.get()['ids']
            if existing_ids:
                print(f"🧹 Eliminando {len(existing_ids)} registros antiguos...")
                # Borramos en lotes para evitar sobrecarga si son muchos
                batch_size = 5000
                for i in range(0, len(existing_ids), batch_size):
                    vector_db.delete(existing_ids[i:i+batch_size])
        except Exception as e:
            print(f"⚠️ Advertencia al limpiar registros (puede ser base nueva): {e}")

        # Insertamos los nuevos fragmentos
        print("💾 Guardando nueva información...")
        vector_db.add_documents(documents=chunks)
        
        print("✅ ChromaDB actualizada con éxito (URLs + PDFs).")
    else:
        print("⚠️ No hay documentos válidos (ni URLs ni PDFs) para entrenar.")
        # Opcional: Si no hay documentos, podrías querer vaciar la DB también
        try:
             embedding_function = OllamaEmbeddings(model=MODELO_EMBEDDING)
             vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
             existing_ids = vector_db.get()['ids']
             if existing_ids:
                 vector_db.delete(existing_ids)
                 print("🧹 Base de datos vaciada (no hay documentos origen).")
        except:
            pass

    return True