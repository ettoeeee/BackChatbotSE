# Importante: Ejecutar esta linea de codigo siempre en la terminal, ya que usamos entorno virtual y las 
# dependencias se instalan temporalmente en el entorno virtual
# pip install -r requirements.txt
# Ejecutar el servidor: python app.py

from flask import Flask, request, jsonify
from wit import Wit
from flask_cors import CORS  # Importa el módulo CORS
import json  # Importa json para manejar el archivo de respuestas
import random  # Importa random para elegir respuestas aleatorias

# Inicializa la aplicación Flask
app = Flask(__name__)

# Habilita CORS para que el frontend pueda hacer solicitudes al backend sin problemas
CORS(app)

# Diccionario para almacenar las sesiones de cada usuario.
# Cada usuario tendrá un 'session_id', un contexto y un historial de conversación.
sessions = {}

# Configura el cliente de Wit.ai con el token de acceso 
wit_client = Wit("LI2J3TBOAOK3U6GICVIRRIUEMYUKSTZZ")

# Cargar respuestas desde el archivo JSON
def load_answers():
    try:
        with open("data/answers.json", "r", encoding="utf-8") as file:
            answers = json.load(file)
            print("Respuestas cargadas correctamente.")
            return answers
    except FileNotFoundError:
        print("Error: El archivo answers.json no fue encontrado.")
        return {}
    except json.JSONDecodeError:
        print("Error: El archivo answers.json tiene un formato incorrecto.")
        return {}

answers = load_answers()

# Ruta principal para interactuar con el chatbot
@app.route("/chat", methods=["POST"])
def chat():
    # Obtener el user_id y el mensaje del usuario desde el frontend
    user_id = request.json.get("user_id")
    user_message = request.json.get("message")  # Obtener el mensaje del usuario desde el frontend

    # Validamos que se haya enviado un user_id
    if not user_id:
        return jsonify({"error": "Se requiere un user_id"}), 400

    # Si el usuario no tiene una sesión activa, la creamos con un contexto vacío y un historial vacío
    if user_id not in sessions:
        sessions[user_id] = {"context": {}, "history": []}

    # Usamos el user_id como session_id para que Wit.ai pueda recordar el contexto de la conversación
    session_id = user_id

    # Enviar el mensaje de usuario a Wit.ai para obtener la respuesta, pasando el session_id (y contexto si fuera necesario)
    response = wit_client.message(user_message, {"session_id": session_id})
    
    # Imprimir la respuesta completa de Wit.ai
    print("Respuesta de Wit.ai:", response)

    # Obtener la intención detectada por Wit.ai
    intents = response.get("intents", [])
    intent_name = intents[0]["name"] if intents else None

    # Imprimir la intención detectada
    print("Intención detectada:", intent_name)

    # Obtener la respuesta desde el archivo JSON según la intención
    if intent_name in answers:
        bot_response = random.choice(answers[intent_name])  # Selecciona una respuesta aleatoria
    else:
        bot_response = "Lo siento, no tengo una respuesta para eso. 🤖"

    # Actualizamos el contexto de la sesión (si Wit.ai devuelve un contexto nuevo, de lo contrario se mantiene el actual)
    sessions[user_id]["context"] = response.get("context", sessions[user_id]["context"])

    # Guardamos el mensaje y la respuesta en el historial de conversación
    sessions[user_id]["history"].append({"user": user_message, "bot": bot_response})

    # Imprimir bot_response antes de enviarlo al frontend
    print("Respuesta del bot:", bot_response)

    # Devolver la respuesta al frontend en formato JSON, junto con el session_id y el historial de la conversación
    return jsonify({"response": bot_response, "session_id": session_id, "history": sessions[user_id]["history"]})

# Ruta para comprobar si el servidor está corriendo correctamente
@app.route("/", methods=["GET"])
def home():
    return "El servidor está corriendo correctamente."

# Inicia el servidor Flask y hace que escuche en todas las interfaces (0.0.0.0) para conexiones externas
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

# Para exponer este servidor públicamente de forma temporal, usa ngrok en otra terminal distinta del servidor:
# cd C:\Users\Jos\Documents\ngrok
# .\ngrok http 8000
