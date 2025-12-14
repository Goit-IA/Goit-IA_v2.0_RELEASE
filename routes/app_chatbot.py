from flask import Blueprint, render_template, request, jsonify
import sys
import os
import traceback # Para ver el error detallado

# --- 1. CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Rutas clave
template_dir = os.path.join(project_root, 'templates')
models_dir = os.path.join(project_root, 'models')
logic_dir = os.path.join(project_root, 'logic') 
data_dir_chroma = os.path.join(project_root, 'data', 'chroma_db_web')

# --- 2. IMPORTACIÓN Y CONFIGURACIÓN ---
selector = None
init_error = "El sistema no se inicializó." # Variable para guardar el error

try:
    # A) Agregar rutas al sistema para que los imports funcionen
    if project_root not in sys.path: sys.path.append(project_root)
    if logic_dir not in sys.path: sys.path.append(logic_dir)
    if models_dir not in sys.path: sys.path.append(models_dir)

    # B) Parchear la ruta de Chroma DB antes de cargar nada
    from models import modelo_llm
    modelo_llm.CHROMA_PATH = data_dir_chroma
    print(f"📂 Ruta Chroma ajustada: {modelo_llm.CHROMA_PATH}")

    # C) Importar y Cargar el Selector desde 'logic'
    # IMPORTANTE: Esto ejecutará 'modelo_knn.py', que buscará 'faq.csv' inmediatamente.
    from logic.seleccion_modelo import SelectorDeModelo

    print("🤖 Cargando Selector...")
    selector = SelectorDeModelo(usar_knn=True, usar_llm=True, umbral_distancia=0.4)
    print("✅ Sistema listo.")
    init_error = None # Limpiamos el error si todo salió bien

except Exception as e:
    # Capturamos cualquier error de importación o archivo no encontrado
    error_trace = traceback.format_exc()
    print(f"❌ ERROR CRÍTICO AL CARGAR: {e}")
    print(error_trace)
    # Guardamos el error para mostrárselo al usuario en el chat
    init_error = f"Error de Servidor: {str(e)}"


# --- 3. DEFINICIÓN DEL BLUEPRINT ---
chatbot_bp = Blueprint('chatbot', __name__, template_folder=template_dir)

@chatbot_bp.route('/chat')
def chat():
    return render_template('chatbot.html', active_page='chat')

@chatbot_bp.route('/api/chat', methods=['POST'])
def api_chat():
    global selector, init_error

    # --- MODO DIAGNÓSTICO ---
    # Si el selector falló al cargar, devolvemos el error como si fuera un mensaje del bot
    # para que puedas leerlo en la pantalla del chat.
    if selector is None:
        mensaje_error = f"⚠️ EL SISTEMA NO CARGÓ.\n\nDetalle: {init_error}\n\nRevisa la terminal para más detalles."
        return jsonify({
            "reply": mensaje_error,
            "model": "Error de Sistema"
        })

    try:
        data = request.json
        pregunta_usuario = data.get('message')

        if not pregunta_usuario:
            return jsonify({"error": "Mensaje vacío."}), 400

        respuesta_generada, fuente_modelo = selector.responder(pregunta_usuario)

        return jsonify({
            "reply": respuesta_generada,
            "model": fuente_modelo
        })

    except Exception as e:
        print(f"Error en api_chat: {e}")
        return jsonify({"reply": f"Ocurrió un error interno: {str(e)}", "model": "Error"}), 500