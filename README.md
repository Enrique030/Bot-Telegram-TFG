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
- Responde a los comandos /start y /help.
- Repite cualquier otro mensaje que le envíes.
- Interacción con botones: El bot puede presentar opciones al usuario a través de botones interactivos.
- Información meteorológica: Al enviar el comando /clima [nombre_de_la_ciudad], el bot proporciona información meteorológica actual de la ciudad especificada.
- Envío de contenido multimedia: El bot puede enviar fotos, audios y stickers a petición del usuario.
- Uso de emojis: El bot puede responder con emojis para hacer la interacción más amena. 

## Conexión con APIs
Este bot utiliza la API de OpenWeatherMap para proporcionar información meteorológica en tiempo real. Asegúrate de obtener tu propia clave API de OpenWeatherMap y reemplazar 'TU_CLAVE_API' en 'main.py' con tu clave.