# Trabajo de Fin de Grado

## 🤖 Bot de Telegram para consultas sobre riesgos laborales de las PYMES

Este es un bot de Telegram que utiliza el modelo de lenguaje de Google Gemini para generar respuestas 
a las preguntas de los usuarios que quieran saber sobre los riesgos laborales de las Pymes en España.

### Autor: Enrique Cogolludo Fernández

## 🖥️ Configuración
1. Clona este repositorio.
2. Instala las dependencias usando pip install -r requirements.txt.
3. Crea un bot en Telegram a través de BotFather y obtén tu token.
4. Reemplaza 'TELEGRAM_TOKEN' en el fichero de variables de entorno '.env' con tu token.
5. Crea una API KEY en la web oficial de Google Gemini <https://gemini.google.com/app?hl=es-ES> y reemplaza
'GOOGLE_API_KEY' en el fichero de variables de entorno '.env' del código con tu API KEY.
6. Ejecuta el bot usando <python bot_chat.py> en tu terminal.
7. Conversa con tu bot de telegram.

## Pasos para crear un bot en Telegram a través de BotFather y obtener tu token propio
1. Descargar la aplicación de Telegram Desktop a través del siguiente enlace <https://desktop.telegram.org/>.
(También puedes usar la aplicación de Telegram desde tu dispositivo móvil descargándola desde la App Store o Play Store).
2. Abre Telegram y en la barra de búsqueda de Telegram, escribe @BotFather, es un bot oficial de Telegram
con una verificación azul.
3. Inicia una conversación con BotFather, haz click en Start o escribe /start.
4. Crea un nuevo bot, escribe el comando, /newbot, BotFather te pedirá dos cosas:
    - El nombre del bot (puedes elegir el que quieras, por ejemplo, Asistente Personal).
    - Nombre del usuario del bot (debe de acabar en bot, por ejemplo AsistentePersonal_bot o MiAsistente123_bot)
5. Una vez completado el paso anterior, BotFather te enviará un mensaje con un token de API. 
Guarda este token en un lugar seguro porque lo necesitarás para interactuar con el bot desde tu código.
6. Configura tu propio bot (opcional):
    - /setdescription - Describe lo que hace tu bot
    - /setbouttext - Texto corto que aparece en la biografía
    - /setuserpic - Cambiar la foto de perfil
    - /setcommands - Definir comandos personalizados (por ejemplo, /ayuda, /start)
7. Ahora tu bot ya está creado y disponible en Telegram. Puedes buscarlo por su nombre de usuario y empezar a hablar con él.

## Pasos para crear una API KEY de Google Gemini
1. Ve a <https://makersuite.google.com/app> 
2. Inicia sesión con tu cuenta de Google o crea una nueva.
3. Accede a la sección API Key en <https://aistudio.google.com/app/apikey>.
4. Haz click en Create API Key. Se generará tu API Key.
5. Reemplaza 'GOOGLE_API_KEY' en el fichero de variables de entorno '.env' del código con tu propia API de Gemini.

## Pasos para crear una API KEY de SerpAPI
1. Ve al sitio oficial de SerpAPI <https://serpapi.com/>
2. Crea una cuenta o inicia sesión
    - Puedes registrarte con email, Google o GitHub.
    - Confirma tu correo si es necesario.
3. Accede a tu API Key, una vez dentro:
    - Ve a tu panel de control (dashboard): <https://serpapi.com/dashboard>.
    - Verás tu API Key personal listada ahí.
    - Reemplaza 'SERPAPI_KEY' en el fichero de variables de entorno '.env' del código con tu propia SerpAPI Key.