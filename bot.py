import os
import logging
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuración del bot
TELEGRAM_BOT_TOKEN = "7845923493:AAGgvXD_zvcqZUAQBi3C-UWm1IMRSikEf7U"
FLASK_SERVER_URL = "http://localhost:5000/procesar"  # URL de la API con HTTPS
API_KEY = os.getenv("API_KEY")  # Asegúrate de definir esta variable de entorno

# Configurar logging para ver errores en consola
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Hola! Soy un bot de riesgos laborales. Pregúntame sobre normativa y prevención.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    consulta = update.message.text
    headers = {"X-API-KEY": API_KEY}
    try:
        response = requests.post(FLASK_SERVER_URL, json={'consulta': consulta}, headers=headers, verify=False)

        if response.status_code == 200:
            respuesta = response.json().get('respuesta', 'No se obtuvo respuesta del servidor.')
        else:
            respuesta = f"Error {response.status_code}: {response.json().get('error', 'Error desconocido')}"

    except Exception:
        respuesta = "No se pudo conectar con el servidor."

    await update.message.reply_text(respuesta)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Ocurrió un error: {context.error}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
