# Importante: Ejecutar esta línea de código siempre en la terminal, ya que usamos entorno virtual y las 
# dependencias se instalan temporalmente en el entorno virtual
# pip install -r requirements.txt
# Ejecutar el servidor: python app.py

from flask import Flask, request, jsonify
from wit import Wit
from flask_cors import CORS  # Importa el módulo CORS
import json
import random 

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

# Respuestas para cuando no se detecta ninguna intención (wrong intents)
wrong_intents_responses = [
    "😕 Lo siento, no entendí eso. ¿Te gustaría saber más sobre alguna de estas opciones? \n 1. Información sobre carreras \n 2. Proyectos del recinto \n 3. Trabajo comunal",
    "🤔 No tengo suficiente información para ayudarte, pero si te interesa, ¿Te gustaría saber más sobre alguna carrera o contacto para consultas?",
    "🙁 No estoy seguro de qué quieres decir. ¿Quizás te interese saber más sobre las oportunidades académicas en la UCR? Aquí tienes algunas opciones: \n 1. Carreras disponibles \n 2. Docencia \n 3. Contactos de la UCR",
    "🤷 Parece que no entendí bien, intenta preguntarlo de otra forma. O tal vez te interese una de estas opciones: \n 1. Detalles sobre la carrera en Informática Empresarial \n 2. Detalles sobre Turismo \n 3. Información del Trabajo Comunal Universitario (TCU)",
    "🔎 No tengo una respuesta para eso, pero estaré encantado de ayudarte en otra cosa. ¿Te gustaría saber más sobre: \n 1. Mercado laboral de alguna carrera \n 2. Proyectos de accion social \n 3. Redes sociales del recinto",
    "🧐 Perdón, no logré comprenderlo. ¿Podrías intentarlo nuevamente con otras palabras? O si lo prefieres, ¿puedo ayudarte con la oferta académica o proporcionarte información sobre la administración del recinto?",
    "🤖 Hmm, no estoy seguro de qué responder. ¿Podrías darme más detalles o elegir alguna de estas opciones? \n 1. Información sobre el Bachillerato en Informática Empresarial \n 2. Carreras ofertadas \n 3. Información sobre el personal docente"
]

# Array con 6 variaciones de mensaje para invitar al usuario a preguntar más
additional_questions_responses = [
    "\n Si tienes más dudas, pregúntame. 🤖",
    "\n Si te queda alguna pregunta, no dudes en consultarme. 💡",
    "\n ¿Tienes alguna otra duda? Estoy aquí para ayudarte. 😊",
    "\n Cualquier otra consulta, solo pregúntame.",
    "\n Si necesitas más información, aquí estoy para ayudarte. 📚",
    "\n No dudes en preguntarme si te surge otra duda.",
    "\n Estoy aquí para responder cualquier otra pregunta que tengas. ✨",
    "\n No dudes en consultarme lo que necesites. 🧐",
    "\n Si tienes más preguntas, dime con confianza.",
    "\n Estoy a tu disposición si necesitas más información. 📖",
    "\n Preguntar es aprender, así que dime si necesitas más ayuda. 🚀"
]


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
        # Si no se detecta una intención válida, usa una respuesta aleatoria de wrong_intents_responses
        bot_response = random.choice(wrong_intents_responses)

    # se concatena un mensaje adicional invitando al usuario a preguntar más.
    if intent_name and intent_name not in ["goodbye", "cultural_extension_project", "social_action_project", "project_definition", "community_service_project", "greetings"]:
        bot_response += " " + random.choice(additional_questions_responses)

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
