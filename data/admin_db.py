# --- admin_db.py ---
import os
import shutil
import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# --- CONFIGURACIÓN ---
CHROMA_PATH = "chroma_db_web"  # Carpeta donde se guardará la BD
MODELO_EMBEDDING = "nomic-embed-text" # Debe estar instalado en Ollama

URLS_A_ESCANEAR = [
    "https://www.uv.mx/estudiantes/tramites-escolares/",
    "https://www.uv.mx/estudiantes/tramites-escolares/tramites-escolares-total/",
    "https://www.uv.mx/estudiantes/tramites-escolares/inscripcion-academico-administrativa/",
    "https://www.uv.mx/estudiantes/tramites-escolares/credencial-estudiante-fisica/",
    "https://www.uv.mx/estudiantes/tramites-escolares/credencial-estudiante-digital/",
    "https://www.uv.mx/estudiantes/tramites-escolares/seguro-facultativo/",
    "https://www.uv.mx/estudiantes/tramites-escolares/examen-de-salud-integral-esi/",
    "https://www.uv.mx/estudiantes/tramites-escolares/cambio-programa-educativo/",
    "https://www.uv.mx/estudiantes/tramites-escolares/reinscripcion-inscripcion-en-linea-il/",
    "https://www.uv.mx/estudiantes/tramites-escolares/declaracion-de-equivalencia-o-revalidacion-de-estudios/",
    "https://www.uv.mx/estudiantes/tramites-escolares/baja-temporal-por-periodo-escolar/",
    "https://www.uv.mx/estudiantes/tramites-escolares/baja-temporal-por-experiencia-educativa/",
    "https://www.uv.mx/estudiantes/tramites-escolares/baja-temporal-extemporanea/",
    "https://www.uv.mx/estudiantes/tramites-escolares/baja-definitiva/",
    "https://www.uv.mx/estudiantes/tramites-escolares/cambio-tutor-academico/",
    "https://www.uv.mx/estudiantes/tramites-escolares/traslado-escolar/",
    "https://www.uv.mx/estudiantes/tramites-escolares/dictamen-para-la-acreditacion-del-idioma-ingles-o-acreditacion-de-la-lengua/",
    "https://www.uv.mx/estudiantes/tramites-escolares/transferencia-de-calificacion-de-ee-a-otro-programa-educativo/",
    "https://www.uv.mx/estudiantes/tramites-escolares/equivalencia-y-o-transferencia-de-calificacion-de-lengua-i-ii-o-ingles-i-ii-al-mismo-programa-educativo-que-cursa-el-alumno/",
    "https://www.uv.mx/estudiantes/tramites-escolares/reconocimiento-de-creditos-por-ee-acreditadas-en-programas-educativos-cursados-previamente/",
    "https://www.uv.mx/estudiantes/tramites-escolares/transferencia-de-creditos-para-el-afel-a-traves-de-las-ee-de-centros-de-idiomas/",
    "https://www.uv.mx/estudiantes/tramites-escolares/movilidad-estudiantil-institucional/",
    "https://www.uv.mx/estudiantes/tramites-escolares/movilidad-estudiantil-nacional/",
    "https://www.uv.mx/estudiantes/tramites-escolares/movilidad-estudiantil-internacional/",
    "https://www.uv.mx/estudiantes/tramites-escolares/cumplimiento-de-servicio-social/",
    "https://www.uv.mx/estudiantes/tramites-escolares/acreditacion-de-la-experiencia-recepcional/",
    "https://www.uv.mx/estudiantes/tramites-escolares/certificado-de-estudios-completo-o-incompleto/",
    "https://www.uv.mx/estudiantes/tramites-escolares/legalizacion-de-certificados-de-estudio/",
    "https://www.uv.mx/estudiantes/tramites-escolares/expedicion-de-titulo-diploma-y-grado-academico/",
    "https://www.uv.mx/estudiantes/tramites-escolares/cedula-profesional/",
    "http://subsegob.veracruz.gob.mx/documentos.php",
    "https://www.uv.mx/estudiantes/tramites-escolares/registro-de-inicio-y-liberacion-del-servicio-social/",
    "https://www.uv.mx/estudiantes/tramites-escolares/autorizacion-de-examen-profesional-o-exencion/",
    "https://www.uv.mx/estudiantes/tramites-escolares/expedicion-de-carta-de-pasante/",
    "https://www.uv.mx/estudiantes/tramites-escolares/autorizacion-de-examen-de-grado/",
    "https://www.uv.mx/dgrf/files/2025/02/Tabulador-de-Cuotas-por-Serv.-Acad.-y-Admvos.-UV-febrero-2025.pdf",
    "https://www.uv.mx/dgae/circulares/",
    "https://www.uv.mx/secretariaacademica/cuotas-del-comite-pro-mejoras/",
    "https://www.uv.mx/legislacion/files/2023/01/RComite%CC%81sProMejoras2023.pdf",
    "https://www.uv.mx/transparencia/ot875/comite-pro-mejoras/",
    "https://www.uv.mx/orizaba/negocios/informes-de-situacion-financiera/",
    "https://www.uv.mx/secretariaacademica/files/2024/09/CIRCULAR-005-2023.pdf",
    "https://www.uv.mx/secretariaacademica/files/2024/11/lineamientos-cuotas-2025.pdf"
]

def raspar_webs():
    print("🕷️  Iniciando Web Scraping...")
    docs = []
    for url in URLS_A_ESCANEAR:
        try:
            if url.lower().endswith('.pdf'): continue
            
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if resp.status_code != 200: continue

            soup = BeautifulSoup(resp.content, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            texto = soup.get_text(separator=' ', strip=True)
            if texto:
                docs.append(Document(page_content=texto, metadata={"source": url}))
                print(f"   ✔ Procesado: {url}")
        except Exception as e:
            print(f"   ❌ Error {url}: {e}")
    return docs

def crear_base_datos():
    # 1. Limpiar BD anterior si existe (para empezar de cero y evitar duplicados)
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print("🗑️  Base de datos anterior eliminada.")

    # 2. Obtener documentos
    documentos = raspar_webs()
    if not documentos:
        print("⚠️ No se encontraron documentos. Revisa las URLs.")
        return

    # 3. Dividir en fragmentos (Chunks)
    print("🔪 Dividiendo texto en fragmentos...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    fragmentos = text_splitter.split_documents(documentos)
    print(f"   -> Se generaron {len(fragmentos)} fragmentos.")

    # 4. Crear y Guardar ChromaDB
    print("💾 Generando Embeddings y guardando en disco (esto tarda un poco)...")
    try:
        Chroma.from_documents(
            documents=fragmentos,
            embedding=OllamaEmbeddings(model=MODELO_EMBEDDING),
            persist_directory=CHROMA_PATH
        )
        print(f"✅ ¡ÉXITO! Base de datos guardada en la carpeta: '{CHROMA_PATH}'")
    except Exception as e:
        print(f"❌ Error al conectar con Ollama: {e}")
        print("Asegúrate de ejecutar 'ollama serve' y 'ollama pull nomic-embed-text'")

if __name__ == "__main__":
    crear_base_datos()