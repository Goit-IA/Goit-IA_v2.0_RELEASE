# Asumiendo que los archivos están en una carpeta 'models'
import sys
import os

# Esto agrega la carpeta raíz del proyecto a las rutas de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.modelo_knn import obtener_respuesta_knn
# --- CORRECCIÓN AQUÍ: Cambiamos 'get_rag_chain' por 'obtener_cadena_rag' ---
from models.modelo_llm import obtener_cadena_rag 

class SelectorDeModelo:
    def __init__(self, usar_knn=True, usar_llm=True, umbral_distancia=0.4):
        """
        Inicializa el selector de modelos.
        """
        self.usar_knn = usar_knn
        self.usar_llm = usar_llm
        self.UMBRAL_DISTANCIA_COSINE = umbral_distancia
        self.rag_chain = None
        
        # Inicializa el modelo LLM (RAG) si está habilitado
        if self.usar_llm:
            try:
                print("Iniciando y cargando el modelo LLM (RAG)...")
                # --- CORRECCIÓN AQUÍ: Llamamos a la función correcta ---
                self.rag_chain = obtener_cadena_rag() 
                print("✅ Modelo LLM listo.")
            except Exception as e:
                print(f"❌ ERROR CRÍTICO al inicializar el modelo LLM: {e}")
                print("El modo LLM se ha desactivado.")
                self.usar_llm = False

    def responder(self, pregunta):
        """
        Genera una respuesta usando KNN con fallback a LLM basado en el umbral.
        """
        
        # --- PASO 1: Intentar con KNN ---
        if self.usar_knn:
            respuesta_knn, distancia = obtener_respuesta_knn(pregunta)
            print(f"DEBUG: Distancia KNN = {distancia:.4f} (Umbral: {self.UMBRAL_DISTANCIA_COSINE})")

            if respuesta_knn and distancia <= self.UMBRAL_DISTANCIA_COSINE:
                return respuesta_knn, "KNN (Coincidencia Alta)"

        # --- PASO 2: Fallback a LLM ---
        if self.usar_llm:
            if not self.rag_chain:
                return "Error: El modelo LLM se activó pero no se inicializó correctamente.", "Error"
            
            try:
                # Usamos .invoke() directamente
                respuesta_llm = self.rag_chain.invoke(pregunta)
                return respuesta_llm, "LLM (RAG)"
            except Exception as e:
                print(f"Error al invocar la cadena RAG: {e}")
                return "Lo siento, ocurrió un error al procesar tu pregunta con el LLM.", "Error LLM"

        return "Lo siento, no tengo una respuesta disponible para esa pregunta.", "Sin Modelo"