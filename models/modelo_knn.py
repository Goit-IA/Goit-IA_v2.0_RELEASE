import pandas as pd
import re
import os  # Necesario para construir la ruta absoluta
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import NearestNeighbors

# --- INICIALIZACIÓN GLOBAL (SE EJECUTA UNA SOLA VEZ) ---

# Descargar stopwords una vez
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Definir stopwords una vez
stop_words_global = set(stopwords.words('spanish'))

# Variables globales para el modelo (se llenarán al inicializar)
knn_model = None
vectorizer = None
respuestas_knn = [] # Lista para guardar las respuestas

def limpiar_texto(texto):
    """Limpia y preprocesa una cadena de texto."""
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    palabras = texto.split()
    # Usamos las stopwords globales ya cargadas
    palabras_filtradas = [p for p in palabras if p not in stop_words_global]
    texto_limpio = ' '.join(palabras_filtradas)
    return texto_limpio

def inicializar_knn():
    """
    Carga los datos y entrena el modelo KNN una sola vez al inicio.
    """
    # Hacemos que esta función modifique las variables globales
    global knn_model, vectorizer, respuestas_knn
    
    try:
        # 1. Obtiene la ruta absoluta de ESTE script (modelo_knn.py)
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 2. Sube un nivel para llegar a la raíz del proyecto (de 'modelo/' a 'mi-chatbot-flask/')
        root_dir = os.path.dirname(script_dir)

        # 3. Construye la ruta completa a 'faq.csv'
        #    (Asumiendo que tu estructura es: mi-chatbot-flask/database/faq.csv)
        ruta_faq = os.path.join(root_dir, 'data', 'faq.csv')
        
        print(f"DEBUG (KNN): Intentando cargar 'faq.csv' desde: {ruta_faq}")

        # 4. Carga los datos usando la ruta absoluta
        df = pd.read_csv(ruta_faq)
        if 'Pregunta' not in df.columns or 'Respuesta' not in df.columns:
            print("Error KNN: El archivo faq.csv no tiene las columnas 'Pregunta' o 'Respuesta'.")
            return

        # 5. Limpia y procesa los datos
        preguntas_limpias = [limpiar_texto(str(p)) for p in df['Pregunta']]
        
        # Guardamos las respuestas en la variable global para referencia futura
        respuestas_knn = df['Respuesta'].tolist()

        # 6. Entrena el Vectorizador
        vectorizer = CountVectorizer()
        X_dataset = vectorizer.fit_transform(preguntas_limpias)

        # 7. Entrena el modelo KNN
        knn_model = NearestNeighbors(n_neighbors=1, metric='cosine')
        knn_model.fit(X_dataset)
        
        print("✅ Modelo KNN cargado y entrenado exitosamente.")

    except FileNotFoundError:
        print(f"❌ ERROR CRÍTICO (KNN): No se pudo encontrar 'faq.csv' en la ruta esperada: {ruta_faq}")
        print("Asegúrate de que tu estructura es: carpeta_raiz/database/faq.csv")
        raise # Relanza el error para detener la inicialización de la app
    except Exception as e:
        print(f"❌ ERROR CRÍTICO (KNN) durante la inicialización: {e}")
        raise

# --- LLAMA A LA INICIALIZACIÓN ---
# Esto se ejecuta UNA SOLA VEZ cuando el archivo es importado por 'seleccion_modelo.py'
inicializar_knn()


def obtener_respuesta_knn(pregunta_usuario):
    """
    Busca la respuesta más cercana usando el modelo KNN YA CARGADO.
    Esta función ahora es muy rápida.
    """
    global knn_model, vectorizer, respuestas_knn
    
    if not knn_model:
        # Si el modelo no se cargó por un error
        return "Error: El modelo KNN no está inicializado.", 1.0

    try:
        # 1. Limpia solo la nueva pregunta
        pregunta_usuario_limpia = limpiar_texto(pregunta_usuario)

        # 2. Transforma la pregunta (NO RE-ENTRENA)
        X_usuario = vectorizer.transform([pregunta_usuario_limpia])

        # 3. Busca el vecino más cercano
        distancias, indices = knn_model.kneighbors(X_usuario)

        indice_respuesta = indices[0][0]
        distancia = distancias[0][0]
        
        # 4. Devuelve la respuesta desde la lista guardada
        respuesta_encontrada = respuestas_knn[indice_respuesta]
        
        return respuesta_encontrada, distancia
    
    except Exception as e:
        print(f"Error en 'obtener_respuesta_knn': {e}")
        return "Error al procesar la pregunta con KNN.", 1.0