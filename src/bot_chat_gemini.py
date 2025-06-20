# Importación de bibliotecas necesarias
import os
import PyPDF2
import google.generativeai as genai
import json
import warnings
import requests

from llama_index.core import VectorStoreIndex, Document
from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv
from telegram.constants import ParseMode

# Ignorar advertencias específicas de enlaces simbólicos en Windows
warnings.filterwarnings("ignore", category=UserWarning, message="To support symlinks on Windows")

# Cargar variables de entorno desde el archivo .env
load_dotenv()
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")    # ID de Telegram
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")        # Clave API de Google
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")        # Token del bot de Telegram
SERPAPI_KEY = os.getenv("SERPAPI_KEY")              # Clave API de SerpAPI

JSON_FILE = "data/conversaciones.json"

PDF_DIRECTORY = "../pdfs"                           # Directorio de archivos PDF

# Configurar la API de Google Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Diccionarios para almacenar mensajes de usuarios y enlaces disponibles
mensajes = {}                    # Historial de mensajes por usuario
pdf_index = None                 # Índice de búsqueda de PDFs
enlaces_disponibles = {}         # Enlaces relevantes cargados

def guardar_en_json(user_id, user_message, bot_response):
    """Función que guarda la conversación del usuario en un archivo JSON"""
    try:
        # Verificar si el archivo JSON existe
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                print("⚠️ Archivo JSON vacío o corrupto, reiniciando.")
                data = {}
        else:
            print("📂 Archivo JSON no encontrado. Creando nuevo.")
            data = {}

        # Asegurar que el user_id esté en los datos
        if str(user_id) not in data:
            data[str(user_id)] = []

        # Agregar la conversación al historial
        data[str(user_id)].append({"usuario": user_message, "bot": bot_response})

        # Guardar los datos actualizados en el archivo JSON
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"✅ Conversación guardada exitosamente en {JSON_FILE} para el usuario: {user_id}")
    except Exception as e:
        print(f"❌ Error al guardar en JSON: {e}")


def handle_user_message(message):
    """Función que almacena los mensajes de los usuarios en el diccionario de mensajes"""
    user_id = message.from_user.id
    if user_id not in mensajes:
        mensajes[user_id] = {"messages": [{"role": "user", "content": message.text}]}
    else:
        mensajes[user_id]["messages"].append({"role": "user", "content": message.text})


def extract_text_from_pdf(pdf_path):
    """Función que extrae el texto de un archivo PDF"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        print(f"❌ Error al leer el PDF {pdf_path}: {str(e)}")
    return text.strip()


def query_pdf_index(index, query):
    """Función que consulta el índice de PDFs y devuelve la respuesta"""
    try:
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        print(f"❌ Error al consultar el índice: {str(e)}")
        return "No se pudo consultar la información de los pdfs"


def get_web_links(query, api_key, num_links=2):
    """Función que obtiene enlaces web dinámicos usando SerpAPI"""
    endpoint = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "num": num_links,
        "hl": "es",  # Resultados en español
        "gl": "es"   # Región de España
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        search_results = response.json()
        links = [(result["title"], result["link"]) for result in search_results.get("organic_results", [])]
        return links[:num_links]
    except Exception as e:
        print(f"❌ Error al obtener enlaces web: {e}")
        return []


def generate_response(message, pdfs_index):
    """Función que genera una respuesta usando Gemini con respuestas concisas y enlaces contextuales"""
    user_id = message.from_user.id
    user_text = message.text.lower()

    if user_id not in mensajes:
        mensajes[user_id] = {"messages": []}

    mensajes[user_id]["messages"].append({"role": "user", "content": user_text})

    # Determinar si la consulta requiere información del índice
    context = ""
    keywords = [
        "riesgos", "laboral", "laborales", "prevención", "seguridad", "salud", "trabajo",
        "ocupacional", "accidente", "enfermedad", "profesional", "físico", "químico",
        "biológico", "ergonómico", "psicosocial", "caída", "atrapamiento", "quemadura",
        "corte", "ruido", "vibración", "estrés", "fatiga", "normativa", "ley", "decreto",
        "reglamento", "31/1995", "486/1997", "39/1997", "773/1997", "compliance",
        "obligación", "inspección", "evaluación", "riesgo", "plan", "medida", "correctiva",
        "preventiva", "formación", "capacitación", "protocolo", "vigilancia", "emergencia",
        "evacuación", "equipo", "protección", "EPI", "maquinaria", "herramienta",
        "instalación", "mantenimiento", "señalización", "PYME", "pequeña", "mediana",
        "empresa", "autónomo", "negocio", "emprendedor", "construcción", "hostelería",
        "industria", "oficina", "comercio", "transporte", "agricultura", "sanidad",
        "taller", "almacén", "trabajador", "empleado", "personal", "contratista",
        "jornada", "turno", "descanso", "exposición", "peligro", "incidente", "ergonomía",
        "psicología", "ventilación", "iluminación", "temperatura, incendio, extintor"
    ]
    if pdfs_index and any(keyword in user_text for keyword in keywords):
        info_rag = query_pdf_index(pdfs_index, user_text)
        context = f"Información adicional de pdfs: {info_rag}\n\n"

    # Construir el historial de la conversación
    conversation_history = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in mensajes[user_id]["messages"]]
    )

    # Preparar la lista de enlaces disponibles para el prompt
    enlaces_texto = "\n".join([f"- {nombre}: {url}" for nombre, url in enlaces_disponibles.items()])

    # Prompt ajustado para incluir enlaces en formato Markdown
    prompt = (
        f"{context}Historia de la conversación:\n{conversation_history}\n\n"
        f"Responde como un consultor experto en riesgos laborales."
        f"Sé claro, conciso y responde SOLO a lo preguntado."
        f"Usa un tono técnico si la pregunta lo requiere, si la respuesta se refiere a normativas, leyes o guías específicas."
        f"Usa un tono más conversacional cuando la pregunta no requiera un contexto técnico para ser más cercano con el usuario."
        f"Sé proactivo para anticiparse a los problemas y necesidades que puedan tener los usuarios preguntándoles al final de la respuesta si quiren saber o profundizar más en el tema que se está tratando."
        f"Si le haces una pregunta al usuario para profundizar más sobre el tema que se está hablando, utiliza la pregunta y la respuesta que te da éste para seguir la conversación. No repitas el mismo mensaje."
        f"Incluye enlaces relevantes de esta lista:\n{enlaces_texto}\n\n"
        f"Limita la respuesta a 100-150 palabras."
        f"Ajusta la respuesta al sector del que se está hablando."
        f"Devuélveme SOLO texto plano, si necesitas enumerar una lista usa guiones (-)."
        f"Evita el formato Markdown con **Palabras**."
        f"Cuando incluyas un enlace, usa el formato Markdown: [Nombre](URL)."
        f"Por ejemplo si el usuario te pide que le muestres las conversaciones de un día en concreto, muéstrale las conversaciones de ese día, en este caso no incluyas el límite de palabras en la respuesta."
        f"Ten la capacidad de entablar una conversación con el usuario si es necesario, respondiendo a las preguntas que te hagan y las que tú le hagas al usuario si éste te confirma que le respondas de alguna forma."
        f"Si el usuario te da una consulta ambigua, responde de forma general."
        f"Si el usuario te da una consulta que no tiene que ver nada con los riesgos laborales, indica que no tienes la capacidad de reponder a esa consulta porque solo eres un experto en riesgos laborales."
    )

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        bot_response = response.text.strip()

        # Limpiar cualquier formato residual
        bot_response = bot_response.replace("*", "")

        # Agregar enlaces web dinámicos usando SerpAPI
        if SERPAPI_KEY:
            search_query = f"{user_text} riesgos laborales OR seguridad laboral OR prevención de riesgos"
            web_links = get_web_links(search_query, SERPAPI_KEY)
            if web_links:
                links_text = "\n".join([f"- [{title}]({url})" for title, url in web_links])
                bot_response += f"\n\nPara más información, consulta estos enlaces:\n{links_text}"

        mensajes[user_id]["messages"].append({"role": "assistant", "content": bot_response})
        guardar_en_json(user_id, user_text, bot_response)
        return bot_response
    except Exception as e:
        return f"❌ Error al generar respuesta: {str(e)}"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Función que maneja los mensajes recibidos en Telegram"""
    print(f"📩 Mensaje recibido del ID: {update.message.chat_id}")
    handle_user_message(update.message)
    response = generate_response(update.message, pdf_index)

    # Dividir la respuesta en fragmentos
    max_length = 4000
    if len(response) > max_length:
        parts = [response[i:i + max_length] for i in range(0, len(response), max_length)]
        for part in parts:
            await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
    else:
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)


async def send_welcome_message(application):
    """Función que envía un mensaje de bienvenida cuando el bot se inicia"""
    welcome_message = (
        "¡Hola, bienvenido! 😊 Soy tu asistente virtual especializado en riesgos laborales."
        "Estoy aquí para ayudarle con cualquier consulta relacionada con la seguridad, "
        "prevención y normativa aplicable a las Pequeñas y Medianas Empresas (PYMEs). ¿En qué "
        "puedo ayudarle hoy?"
    )
    await application.bot.send_message(chat_id=TELEGRAM_USER_ID, text=welcome_message)


def initialize_pdf_index():
    """Función que inicializa el índice de PDFs usando embeddings de Hugging Face y el LLM de Gemini"""
    global pdf_index
    if not os.path.exists(PDF_DIRECTORY):
        print(f"⚠️ El directorio '{PDF_DIRECTORY}' no existe.")
        return

    pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"⚠️ No se encontraron PDFs en '{PDF_DIRECTORY}'.")
        return

    print(f"📂 Encontrados {len(pdf_files)} PDFs. Procesando...")
    documents = []
    for file in pdf_files:
        file_path = os.path.join(PDF_DIRECTORY, file)
        text = extract_text_from_pdf(file_path)
        if text.strip():
            documents.append(Document(text=text))
            print(f"✅ Texto extraído de '{file}' ({len(text)} caracteres).")
        else:
            print(f"⚠️ El PDF '{file}' no tiene texto extraíble.")

    if not documents:
        print("❌ No se pudo extraer texto de ningún PDF.")
        return

    try:
        # Configurar el modelo de embeddings
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Configurar el LLM como GoogleGenAI
        Settings.llm = GoogleGenAI(model="gemini-2.0-flash-lite", api_key=GOOGLE_API_KEY)
        pdf_index = VectorStoreIndex.from_documents(documents)
        print("✅ Índice de PDFs cargado exitosamente.")
    except Exception as e:
        print(f"❌ Error al crear el índice: {str(e)}")


def main():
    """Función principal para inicializar el bot y sus componentes"""
    global enlaces_disponibles
    initialize_pdf_index()

    # Cargar enlaces desde el archivo JSON
    try:
        with open("../enlaces.json", "r", encoding="utf-8") as f:
            enlaces_disponibles = json.load(f)
        print(f"✅ Enlaces cargados: {len(enlaces_disponibles)} enlaces disponibles.")
    except Exception as e:
        print(f"❌ Error al cargar enlaces.json: {e}")

    # Configurar y ejecutar el bot de Telegram
    bot = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(send_welcome_message) \
        .build()

    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("🤖 El bot está en ejecución...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()