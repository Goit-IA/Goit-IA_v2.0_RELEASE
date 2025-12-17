from flask import Blueprint, render_template, request, jsonify
import sys
import os
import re
import csv
import pandas as pd

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
template_dir = os.path.join(project_root, 'templates')
logic_dir = os.path.join(project_root, 'logic') 
models_dir = os.path.join(project_root, 'models')
data_dir_chroma = os.path.join(project_root, 'data', 'chroma_db_web')
csv_path = os.path.join(project_root, 'data', 'faq.csv')

# Imports de lógica
if project_root not in sys.path: sys.path.append(project_root)

# Importamos el módulo completo de KNN para poder recargarlo
from models import modelo_knn 
from models import modelo_llm
modelo_llm.CHROMA_PATH = data_dir_chroma
from logic.seleccion_modelo import SelectorDeModelo

# --- NUEVO IMPORT PARA EL REGISTRO DE ACCESOS ---
from logic.access_tracker import registrar_acceso

# Inicialización
selector = None
try:
    selector = SelectorDeModelo(usar_knn=True, usar_llm=True)
except Exception as e:
    print(f"Error al iniciar selector: {e}")

chatbot_bp = Blueprint('chatbot', __name__, template_folder=template_dir)

# Variables globales
historial_conversacion = [] 
ultima_pregunta = ""

# --- FUNCIONES AUXILIARES ---

def limpiar_texto_markdown(texto):
    if not texto: return ""
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.*?)\*', r'\1', texto)
    texto = re.sub(r'^\s*[\+\-\*]\s+', '• ', texto, flags=re.MULTILINE)
    texto = re.sub(r'```', '', texto)
    return texto.strip()

def guardar_faq_csv(pregunta, respuesta):
    """Guarda una NUEVA pregunta (Append)."""
    try:
        with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([pregunta, respuesta])
        print(f"💾 Guardado nuevo en CSV.")
    except Exception as e:
        print(f"Error guardando CSV: {e}")

def reemplazar_faq_csv(pregunta, nueva_respuesta):
    """Actualiza una respuesta existente en el CSV."""
    try:
        df = pd.read_csv(csv_path)
        mask = df['Pregunta'] == pregunta
        
        if mask.any():
            # Actualizar última coincidencia
            idx = df[mask].last_valid_index()
            df.at[idx, 'Respuesta'] = nueva_respuesta
            df.to_csv(csv_path, index=False)
            print(f"🔄 CSV Actualizado: Respuesta reemplazada para '{pregunta[:15]}...'")
            return True
        else:
            # Si no existe, guardar como nueva
            guardar_faq_csv(pregunta, nueva_respuesta)
            return True
            
    except Exception as e:
        print(f"Error actualizando CSV: {e}")
        return False

def formatear_historial(lista_historial):
    texto_historial = ""
    for msj in lista_historial[-5:]: 
        role = "Usuario" if msj['role'] == 'user' else "Asistente"
        texto_historial += f"{role}: {msj['content']}\n"
    return texto_historial

def formatear_texto_html(texto):
    """
    Convierte Markdown a HTML unificando todas las listas a viñetas (•)
    y corrigiendo el problema del primer elemento con guion.
    """
    if not texto: return ""
    
    texto = texto.strip()

    # 1. Negritas (**texto**)
    texto = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', texto)
    
    # 2. Títulos (### texto)
    texto = re.sub(r'###\s*(.*?)(?:\n|$)', r'<br><span class="chat-title">\1</span><br>', texto)
    
    # --- CORRECCIÓN CLAVE ---
    # 3. Detectar si hay un guion/viñeta pegado a unos dos puntos (ej: "necesario: - Generar")
    # Forzamos un salto de línea antes del guion para que la regla de abajo lo detecte.
    texto = re.sub(r':\s*([\-\*•])', r':\n\1', texto)

    # 4. UNIFICACIÓN DE LISTAS
    # Detecta guiones (-), asteriscos (*) O viñetas existentes (•) al inicio de una línea
    # y los transforma TODOS al formato HTML correcto (<br>• ).
    texto = re.sub(r'(?m)^\s*[\-\*•]\s+(.*)', r'<br>• \1', texto)

    # 5. Listas Numeradas (1. Item)
    texto = re.sub(r'(?m)^\s*(\d+)\.\s+(.*)', r'<br>\1. \2', texto)
    
    # 6. Separación de párrafos (Puntos y aparte)
    # Agrega espacio extra si hay punto, pero NO si es parte de una lista.
    texto = re.sub(r'(?<!\d)(?<!•)\.\s+(?=[A-Z¿¡])', '.<br><br>', texto)

    # Limpieza final
    return texto.strip()

# --- RUTAS ---

@chatbot_bp.route('/chat')
def chat():
    global historial_conversacion
    historial_conversacion = [] 
    return render_template('chatbot.html')

@chatbot_bp.route('/api/chat', methods=['POST'])
def api_chat():
    global selector, historial_conversacion, ultima_pregunta

    data = request.json
    modo = data.get('mode', 'normal') 
    
    # 1. Gestión de la pregunta
    if modo == 'regenerate':
        if not ultima_pregunta:
            return jsonify({"error": "No hay pregunta anterior"}), 400
        pregunta_usuario = ultima_pregunta
        
        # Eliminar respuesta anterior del historial
        if historial_conversacion and historial_conversacion[-1]['role'] == 'assistant':
            historial_conversacion.pop()
            
        # Forzar LLM
        forzar_llm = True
        print(f"🤖 MODO REGENERAR: Forzando LLM para '{pregunta_usuario}'")
            
    else:
        pregunta_usuario = data.get('message')
        ultima_pregunta = pregunta_usuario
        forzar_llm = False

    if not pregunta_usuario:
        return jsonify({"error": "Mensaje vacío"}), 400

    # 2. Generar respuesta
    contexto_str = formatear_historial(historial_conversacion)
    
    # AQUÍ PASAMOS EL FLAG forzar_llm
    respuesta_raw, fuente = selector.responder(pregunta_usuario, contexto_str, forzar_llm=forzar_llm)
    
    respuesta_limpia = formatear_texto_html(respuesta_raw)

    # 3. Guardar en Historial Sesión
    if modo == 'normal':
        historial_conversacion.append({"role": "user", "content": pregunta_usuario})
    
    historial_conversacion.append({"role": "assistant", "content": respuesta_limpia})

    # 4. LÓGICA DE ACTUALIZACIÓN DEL SISTEMA (Caché Semántico)
    if respuesta_limpia and "Error" not in fuente:
        
        if modo == 'regenerate':
            # A) Reemplazar en CSV
            exito_csv = reemplazar_faq_csv(pregunta_usuario, respuesta_limpia)
            
            # B) RE-ENTRENAR KNN (Actualizar Caché Semántico)
            if exito_csv:
                print("🧠 Actualizando Caché Semántico (KNN)...")
                modelo_knn.inicializar_knn() # Recarga el modelo en memoria
                
        else:
            # Si fue respuesta de LLM en modo normal, la guardamos también
            if "LLM" in fuente:
                guardar_faq_csv(pregunta_usuario, respuesta_limpia)
                # Opcional: Recargar KNN aquí también si quieres aprendizaje instantáneo en modo normal
                modelo_knn.inicializar_knn()

    return jsonify({
        "reply": respuesta_limpia,
        "model": fuente
    })

# --- NUEVA RUTA: REGISTRO DE ACCESOS ---

@chatbot_bp.route('/api/register_access', methods=['POST'])
def register_access():
    data = request.json
    programa = data.get('programa')
    
    if not programa:
        return jsonify({"status": "error", "message": "Programa no seleccionado"}), 400

    # Obtener IP (Manejo de Proxy si existe, sino remote_addr)
    if request.headers.getlist("X-Forwarded-For"):
        user_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        user_ip = request.remote_addr
        
    user_agent = request.headers.get('User-Agent')

    # Guardar usando la lógica importada
    try:
        registrar_acceso(programa, user_ip, user_agent)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error registrando acceso: {e}")
        return jsonify({"status": "error", "message": "Error interno al guardar"}), 500