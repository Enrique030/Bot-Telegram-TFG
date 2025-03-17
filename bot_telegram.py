
import telebot
import requests
# import openai

from constantes import *
from telebot import types
# from newsapi import NewsApiClient

# Token para conexión con nuestro BOT
TOKEN = '7845923493:AAGgvXD_zvcqZUAQBi3C-UWm1IMRSikEf7U'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['chiste'])
def send_joke(message):
    """Función para obtener y enviar un chiste aleatorio desde JokeAPI"""
    params = {
        "format": "json",
        "lang": "es",  # Se puede cambiar a "en" para chistes en inglés
        "type": "any"  # Puede ser "single" (una sola línea) o "twopart" (pregunta-respuesta)
    }

    response = requests.get(BASE_URL_JOKE, params=params)
    joke_data = response.json()

    if joke_data.get("error"):
        bot.reply_to(message, "Lo siento, no pude encontrar un chiste ahora mismo.")
        return

    # Formateamos el chiste dependiendo de su tipo
    if joke_data["type"] == "single":
        joke_text = joke_data["joke"]
    else:  # type == "twopart"
        joke_text = f"{joke_data['setup']}\n\n{joke_data['delivery']}"

    bot.reply_to(message, joke_text)


@bot.message_handler(commands=['gif'])
def send_gif(message):
    """Función para recibir un GIF basado en una palabra clave"""
    if len(message.text.split()) > 1:
        query = message.text.split(maxsplit=1)[1]
    else:
        query = "random"

    params = {
        "api_key": API_KEY_GIPHY,
        "q": query,
        "limit": 1,
        "rating": "g",
        "lang": "es"
    }

    response = requests.get(BASE_URL_GIPHY, params=params)
    data = response.json()

    if data.get("data"):
        gif_url = data["data"][0]["images"]["original"]["url"]
        bot.send_animation(message.chat.id, gif_url)
    else:
        bot.reply_to(message, "No encontré ningún GIF para esa búsqueda")


'''
openai.api_key = API_KEY_OPENAI

def get_openai_response(prompt):
    """Función para obtener una respuesta de la API de OpenAI."""
    try:
        response = openai.Completion.create(
            engine="gpt-4o",  # Se puede elegir otro modelo
            prompt=prompt,
            max_tokens=150  # Ajustamos según sea necesario
        )
        return response.choices[0].text.strip()

    except Exception as e:
        print(f"Error al obtener respuesta de OpenAI: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Manejador de mensajes para interactuar con la API de OpenAI."""
    response = get_openai_response(message.text)
    bot.reply_to(message, response)
'''

@bot.message_handler(commands=['news'])
def send_news(message):
    """Función para obtener las últimas noticias"""
    params = {
        "apiKey": API_KEY_NEWS,
        "country": "us",  # Para cambiar el país (ejemplo: 'es' para España)
        "category": "sports",  # Opcional: se puede cambiar la categoría
        "pageSize": 5  # Número de noticias a obtener
    }

    # Hacemos una solicitud GET
    response = requests.get(f"{BASE_URL_NEWS}v2/top-headlines", params=params)
    data = response.json()

    if data.get("status") == "ok":
        articles = data.get("articles", [])
        if not articles:
            bot.reply_to(message, "No se encontraron noticias en este momento.")
            return

        news_text = "📰 Últimas noticias:\n\n"
        for article in articles:
            title = article["title"]
            url = article["url"]
            news_text += f"🔹 <b>{title}</b>\n<a href='{url}'>Ver más</a>\n\n"

        bot.send_message(message.chat.id, news_text, parse_mode="HTML")
    else:
        bot.reply_to(message, "Hubo un problema al obtener las noticias. Inténtalo más tarde.")


def get_weather(city_name):
    """Función que utiliza la API OpenWeatherMap para saber el clima
    de una ciudad en específico"""
    complete_url = f"{BASE_URL_WEATHER}q={city_name}&appid={API_KEY_WEATHER}&lang=es&units=metric"

    # Hacemos una solicitud GET
    response = requests.get(complete_url)
    data = response.json()
    print(data)

    if data.get("cod") != 404:
        main_data = data["main"]
        weather_data = data["weather"][0]
        temperature = main_data["temp"]
        description = weather_data["description"]
        return f"Temperatura: {temperature:.2f}°C\n{description.capitalize()}"
    else:
        return 'Ciudad no encontrada'


@bot.message_handler(commands=['clima'])
def send_weather(message):
    """Función para saber el clima de una ciudad utilizando el comando /clima + ciudad
    Esta función utiliza la función get_weather(city_name) y su API correspondiente"""
    city_name = message.text.split()[1] if len(message.text.split()) > 1 else None
    if city_name:
        weather_info = get_weather(city_name)
        bot.reply_to(message, weather_info)
    else:
        bot.reply_to(message, "Por favor, proporciona el nombre de la ciudad. Ejemplo: /clima Madrid")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Función inicial para que el bot salude utilizando el comando /start"""
    bot.reply_to(message, 'Hola! Soy tu primer bot creado con Telebot')



@bot.message_handler(commands=['help'])
def send_help(message):
    """Función para ver las instrucciones del bot utilizando el comando /help
    Qué es lo que realmente puede hacer el bot"""
    bot.reply_to(message, 'Puedes interactuar conmigo usando comandos. '
                          'Por ahora, solo respondo a /start, /help, /pizza, /foto, /clima <ciudad>, /news, /gif <palabra_clave> y /chiste.')


# @bot.message_handler(func=lambda m: True)
# def echo_all(message):
    # """Función en la que el bot te responde con lo mismo que le has escrito"""
     # bot.reply_to(message, message.text)


@bot.message_handler(commands=['pizza'])
def send_options(message):
    """Función random para probar los botones"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Creamos los botones
    btn_si = types.InlineKeyboardButton('Si', callback_data='pizza_si')
    btn_no = types.InlineKeyboardButton('No', callback_data='pizza_no')

    # Agregamos los botones al markup
    markup.add(btn_si, btn_no)

    # Enviamos el mensaje con los botones
    bot.send_message(message.chat.id, "¿Te gusta la pizza?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    if call.data == 'pizza_si':
        bot.answer_callback_query(call.id, '¡A mi tambien!')
    elif call.data == 'pizza_no':
        bot.answer_callback_query(call.id, '¡Bueno cada uno tienes sus gustos!')


@bot.message_handler(commands=['foto'])
def send_image(message):
    """Función que dado el comando /foto el bot te envía la imagen propuesta"""
    img_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png'
    bot.send_photo(chat_id=message.chat.id, photo=img_url, caption='Aqui tienes tu imagen')


if __name__ == "__main__":
    bot.polling(none_stop=True)
