import pandas as pd
import re
import os
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import NearestNeighbors

# --- INICIALIZACIÓN GLOBAL ---

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

stop_words_global = set(stopwords.words('spanish'))

# Variables globales
knn_model = None
vectorizer = None
respuestas_knn = []

def limpiar_texto(texto):
    """Limpia y preprocesa una cadena de texto."""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    palabras = texto.split()
    palabras_filtradas = [p for p in palabras if p not in stop_words_global]
    return ' '.join(palabras_filtradas)

def inicializar_knn():
    """
    Carga los datos y entrena (o re-entrena) el modelo KNN.
    Esta función se llamará al inicio y cada vez que actualicemos el CSV.
    """
    global knn_model, vectorizer, respuestas_knn
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)
        ruta_faq = os.path.join(root_dir, 'data', 'faq.csv')
        
        print(f"🔄 (KNN) Entrenando/Actualizando modelo con datos de: {ruta_faq}")

        df = pd.read_csv(ruta_faq)
        
        # Validación básica
        if 'Pregunta' not in df.columns or 'Respuesta' not in df.columns:
            print("❌ Error KNN: Columnas faltantes en faq.csv")
            return

        # Limpieza
        preguntas_limpias = [limpiar_texto(str(p)) for p in df['Pregunta']]
        respuestas_knn = df['Respuesta'].tolist()

        # Entrenamiento
        vectorizer = CountVectorizer()
        X_dataset = vectorizer.fit_transform(preguntas_limpias)

        knn_model = NearestNeighbors(n_neighbors=1, metric='cosine')
        knn_model.fit(X_dataset)
        
        print(f"✅ Modelo KNN actualizado. Total de conocimientos en caché: {len(respuestas_knn)}")

    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo {ruta_faq}")
    except Exception as e:
        print(f"❌ Error al entrenar KNN: {e}")

# Carga inicial
inicializar_knn()

def obtener_respuesta_knn(pregunta_usuario):
    global knn_model, vectorizer, respuestas_knn
    
    if not knn_model:
        return None, 1.0

    try:
        pregunta_usuario_limpia = limpiar_texto(pregunta_usuario)
        X_usuario = vectorizer.transform([pregunta_usuario_limpia])
        distancias, indices = knn_model.kneighbors(X_usuario)

        indice_respuesta = indices[0][0]
        distancia = distancias[0][0]
        
        respuesta_encontrada = respuestas_knn[indice_respuesta]
        return respuesta_encontrada, distancia
    
    except Exception as e:
        print(f"Error KNN query: {e}")
        return None, 1.0