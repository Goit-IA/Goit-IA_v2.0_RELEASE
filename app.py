from flask import Flask

# Importar los Blueprints
from routes.app_inicio import inicio_bp
from routes.app_chatbot import chatbot_bp
from routes.app_informacion import informacion_bp
from routes.app_acercade import acercade_bp
from routes.app_privacidad import privacidad_bp

# Crear la instancia de la aplicación Flask
app = Flask(__name__)

# Registrar los Blueprints en la aplicación
app.register_blueprint(inicio_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(informacion_bp)
app.register_blueprint(acercade_bp)
app.register_blueprint(privacidad_bp)

# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)