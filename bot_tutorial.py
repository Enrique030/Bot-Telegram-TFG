
import telebot
import requests

from telebot import types

#Conexion con nuestro BOT
TOKEN = '7845923493:AAGgvXD_zvcqZUAQBi3C-UWm1IMRSikEf7U'
API_KEY = '1d2f61f9e0f17884c9fcfd8b7f87830c'

bot = telebot.TeleBot(TOKEN)
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather?'


def get_weather(city_name):
    complete_url = f"{BASE_URL}q={city_name}&appid={API_KEY}&lang=es&units=metric"
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
    city_name = message.text.split()[1] if len(message.text.split()) > 1 else None
    if city_name:
        weather_info = get_weather(city_name)
        bot.reply_to(message, weather_info)
    else:
        bot.reply_to(message, "Por favor, proporciona el nombre de la ciudad. Ejemplo: /clima Madrid")


#Creacion de comandos simples como `/start` y `/help`
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Hola! Soy tu primer bot creado con Telebot')



@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'Puedes interactuar conmigo usando comandos. Por ahora, solo respondo a /start y /help')


# @bot.message_handler(func=lambda m: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)


@bot.message_handler(commands=['pizza'])
def send_options(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Creando botones
    btn_si = types.InlineKeyboardButton('Si', callback_data='pizza_si')
    btn_no = types.InlineKeyboardButton('No', callback_data='pizza_no')


    #Agrega botones al markup
    markup.add(btn_si, btn_no)


    #Enviar mensaje con los botones
    bot.send_message(message.chat.id, "¿Te gusta la pizza?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    if call.data == 'pizza_si':
        bot.answer_callback_query(call.id, '¡A mi tambien!')
    elif call.data == 'pizza_no':
        bot.answer_callback_query(call.id, '¡Bueno cada uno tienes sus gustos!')


@bot.message_handler(commands=['foto'])
def send_image(message):
    img_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png'
    bot.send_photo(chat_id=message.chat.id, photo=img_url, caption='Aqui tienes tu imagen')


if __name__ == "__main__":
    bot.polling(none_stop=True)
