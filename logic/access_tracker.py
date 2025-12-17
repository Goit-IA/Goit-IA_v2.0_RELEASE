import os
import csv
import pandas as pd
from datetime import datetime

# Definir ruta del archivo CSV
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
DATA_DIR = os.path.join(project_root, 'data')
CSV_FILE = os.path.join(DATA_DIR, 'access_log.csv')

def registrar_acceso(programa, ip, dispositivo):
    """
    Guarda el registro de acceso en el CSV.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    archivo_existe = os.path.exists(CSV_FILE)
    ahora = datetime.now()
    
    datos = [
        ahora.strftime('%A'),           # Día
        ahora.strftime('%Y-%m-%d'),     # Fecha
        ahora.strftime('%H:%M:%S'),     # Hora
        programa,                       # Programa
        dispositivo,                    # Dispositivo
        ip                              # IP
    ]
    
    cabeceras = ['Dia', 'Fecha', 'Hora', 'Programa', 'Dispositivo', 'IP']

    try:
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not archivo_existe:
                writer.writerow(cabeceras)
            writer.writerow(datos)
        print(f"✅ Acceso registrado: {programa}")
        return True
    except Exception as e:
        print(f"❌ Error registrando acceso: {e}")
        return False

def obtener_estadisticas_diarias():
    """Devuelve el conteo para las gráficas."""
    if not os.path.exists(CSV_FILE):
        return {}
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return {}
        return df['Programa'].value_counts().to_dict()
    except Exception as e:
        return {}

def obtener_todos_los_registros():
    """
    Lee el CSV completo y lo devuelve como una lista de diccionarios
    para mostrar en la tabla detallada.
    """
    if not os.path.exists(CSV_FILE):
        return []
        
    try:
        # Leemos el CSV
        df = pd.read_csv(CSV_FILE)
        
        # Ordenamos por fecha y hora descendente (lo más nuevo primero)
        # Si da error al ordenar (por formatos), simplemente lo devolvemos tal cual
        try:
            df = df.sort_values(by=['Fecha', 'Hora'], ascending=False)
        except:
            pass
            
        # Reemplazamos valores vacíos (NaN) por texto vacío para que no rompa el HTML
        df = df.fillna('')
        
        # Convertimos a lista de diccionarios
        return df.to_dict('records')
    except Exception as e:
        print(f"❌ Error leyendo registros detallados: {e}")
        return []