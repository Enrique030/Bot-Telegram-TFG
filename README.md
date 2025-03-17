# Trabajo de Fin de Grado

## Desarrollo de un bot de Telegram para consultas sobre los riesgos laborales y su normativa

### Autor: Enrique Cogolludo Fernández

#### Este repositorio contiene el código para crear un bot de Telegram utilizando la biblioteca Telebot de Python.

## Configuración
1. Clona este repositorio.
2. Instala las dependencias usando pip install -r requirements.txt.
3. Crea un bot en Telegram a través de BotFather y obtén tu token.
4. Reemplaza 'TU_TOKEN_AQUI' en 'main.py' con tu token.
5. Ejecuta el bot usando python main.py.

## Funcionalidades:
- Responde a los comandos /start, /help, /pizza, /foto, /clima <ciudad>, /news, /gif <palabra_clave> y /chiste.
- Repite cualquier otro mensaje que le envíes. (Lo he quitado, no tiene utilidad)
- Interacción con botones: El bot puede presentar opciones al usuario a través de botones interactivos.
- Información meteorológica: Al enviar el comando /clima [nombre_de_la_ciudad], el bot proporciona información meteorológica actual de la ciudad especificada.
- En construcción -> API de OpenAI (API muy interesante con la que se pueden hacer muchas cosas)
- Envío de contenido multimedia: El bot puede enviar fotos, audios y stickers a petición del usuario. (Falta implementarlo)
- Uso de gifs: El bot puede responder con gifs para hacer la interacción más amena.
- Envío de chistes -> JokeAPI. El bot puede enviar chistes aleatorios con el comando /chiste, aunque se puede especificar la categoría de los chistes que el bot envía

## Conexión con APIs
Este bot utiliza la API de OpenWeatherMap para proporcionar información meteorológica en tiempo real.

También utiliza la API de News API para acceder a noticias de diferentes fuentes. (Esta API no me convence mucho porque solo da noticias de algunas categorías y de algunos países en específico aunque tenga soporte para casi todos. Creo que no es de mucha utilidad e importancia.)

El bot utiliza la API de GIPHY API para enviar GIFS al chat según la palabra específica. Comando: /gif <palabra_clave>

El bot utiliza la API de JokeAPI para enviar chistes aleatorios con el comando /chiste. Aunque se le puede especificar la categoría de los chistes que manda.
Categorías disponibles: Any, Misc, Programming, Dark, Pun, Spooky, Christmas