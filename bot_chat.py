
import os
import requests
import json

from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
JSON_FILE = "conversaciones.json"

# Almacenamos los mensajes de los usuarios
mensajes = {}


def guardar_en_json(user_id, user_message, bot_response):
    """Función para guardar un mensaje en un JSON"""
    try:
        # Intentamos cargar el archivo si existe
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)  # Intentamos cargar el JSON
            except json.JSONDecodeError:
                print("⚠️ Archivo JSON vacío o corrupto, se reiniciará.")
                data = {}  # Si hay un error, se inicializa un diccionario vacío
        else:
            data = {}

        # Agregamos una nueva conversación
        if str(user_id) not in data:
            data[str(user_id)] = []

        data[str(user_id)].append({"usuario": user_message, "bot": bot_response})

        # Guardamos en el archivo JSON
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"✅ Conversación guardada en JSON: {user_id}")

    except Exception as e:
        print(f"❌ Error guardando en JSON: {e}")


def handle_user_message(message):
    """Función que guarda el mensaje del usuario"""
    user_id = message.from_user.id

    if user_id not in mensajes:
        mensajes[user_id] = {"messages": [{"role": "user", "content": message.text}]}
    else:
        mensajes[user_id]["messages"].append({"role": "user", "content": message.text})


def generate_response(message):
    """Función que genera la respuesta del bot usando Mistral AI"""
    user_id = message.from_user.id

    # Guardamos el mensaje original del usuario
    user_text = message.text
    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral-tiny",  # Se puede cambiar a mistral-small (Más preciso, pero algo más lento)
                                  # o mistral-medium (Mejor calidad de respuesta, pero más consumo)
        "messages": mensajes[user_id]["messages"]
        # "max_tokens": 100 -> para limitar la longitud de la respuesta
        # "temeperature": 0.3 -> para ajustar la precisión del bot, etc)
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        bot_response = response_data["choices"][0]["message"]["content"]

        mensajes[user_id]["messages"].append({"role": "assistant", "content": bot_response})

        # Guardamos la conversación en un JSON
        guardar_en_json(user_id, user_text, bot_response)

        return bot_response
    else:
        return f"Error en la API de Mistral: {response.text}"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Función asíncrona para manejar los mensajes en Telegram"""
    print(f"ID del usuario: {update.message.chat_id}")
    handle_user_message(update.message)
    response = generate_response(update.message)
    await update.message.reply_text(response)


async def send_welcome_message(application):
    """Función que envía un mensaje de bienvenida al iniciar el bot"""
    USER_ID = "7568207284"  # Reemplaza con el ID del usuario o grupo al que quieres enviar el mensaje.
    welcome_message = ("¡Hola, encantado de conocerte! 😊 Soy Prevencio-Bot, el bot que sabe todo sobre los"
                       "riesgos laborales. Pregúntame lo que quieras, estoy aquí para ayudarte")

    await application.bot.send_message(chat_id=USER_ID, text=welcome_message)


def main():
    """Función principal"""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    # Configuramos el bot con post_init para enviar el mensaje automático
    bot = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(send_welcome_message) \
        .build()

    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    bot.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()
