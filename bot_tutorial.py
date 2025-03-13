
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram import Update


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola, soy un bot de prueba. Tu mensaje fue " + update.message.text)


def main():
    # Creamos el bot
    bot = Application.builder().token("7845923493:AAGgvXD_zvcqZUAQBi3C-UWm1IMRSikEf7U").build()

    # Función que se ejecuta cuando se recibe un mensaje
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Ejecutamos el bot
    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()