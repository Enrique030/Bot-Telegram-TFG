import os
import PyPDF2
import google.generativeai as genai
import json
from llama_index.core import VectorStoreIndex, Document
from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv
from telegram.constants import ParseMode

import warnings

warnings.filterwarnings("ignore", category=UserWarning, message="To support symlinks on Windows")

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
JSON_FILE = "conversaciones.json"
PDF_DIRECTORY = "documentos"

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Store user messages and available links
mensajes = {}
pdf_index = None
enlaces_disponibles = {}


def guardar_en_json(user_id, user_message, bot_response):
    """Function to save a message in a JSON"""
    try:
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Empty or corrupted JSON file, it will be reset.")
                data = {}
        else:
            data = {}

        if str(user_id) not in data:
            data[str(user_id)] = []

        data[str(user_id)].append({"usuario": user_message, "bot": bot_response})

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"✅ Conversation saved in JSON: {user_id}")
    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")


def handle_user_message(message):
    """Function to handle user messages"""
    user_id = message.from_user.id
    if user_id not in mensajes:
        mensajes[user_id] = {"messages": [{"role": "user", "content": message.text}]}
    else:
        mensajes[user_id]["messages"].append({"role": "user", "content": message.text})


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {str(e)}")
    return text.strip()


def query_pdf_index(index, query):
    """Query the index and return the response"""
    try:
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        print(f"Error querying index: {str(e)}")
        return "No se pudo consultar la información de los documentos."


def generate_response(message, pdf_index):
    """Generate response using Gemini with concise, focused answers and contextual links"""
    user_id = message.from_user.id
    user_text = message.text.lower()

    if user_id not in mensajes:
        mensajes[user_id] = {"messages": []}

    mensajes[user_id]["messages"].append({"role": "user", "content": user_text})

    # Determinar si la consulta requiere información del índice
    context = ""
    keywords = [
        "riesgos", "laboral", "laborales", "prevención", "seguridad", "salud", "trabajo",
        "normativa", "ley", "decreto", "reglamento", "31/1995", "PYME"
    ]
    if pdf_index and any(keyword in user_text for keyword in keywords):
        info_rag = query_pdf_index(pdf_index, user_text)
        context = f"Información adicional de documentos: {info_rag}\n\n"

    # Construir historial de conversación
    conversation_history = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in mensajes[user_id]["messages"]]
    )

    # Preparar lista de enlaces para el prompt
    enlaces_texto = "\n".join([f"- {nombre}: {url}" for nombre, url in enlaces_disponibles.items()])

    # Prompt ajustado para incluir enlaces contextualmente
    prompt = (
        f"{context}Historia de la conversación:\n{conversation_history}\n\n"
        f"Responde como un consultor experto en riesgos laborales. Sé claro, conciso y responde SOLO a lo preguntado. "
        f"Usa un tono técnico si la pregunta lo requiere. Si la respuesta se refiere a normativas, leyes o guías específicas, "
        f"incluye enlaces relevantes de esta lista:\n{enlaces_texto}\n\n"
        f"Limita la respuesta a 100-150 palabras. Devuélveme SOLO texto plano, si necesitas enumerar una lista usa guiones (-). "
        f"Evita el formato Markdown con **Palabras**. Cuando incluyas un enlace, usa el formato 'Nombre (URL)'."
    )

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        bot_response = response.text.strip()

        # Limpiar cualquier formato residual
        bot_response = bot_response.replace("*", "")

        mensajes[user_id]["messages"].append({"role": "assistant", "content": bot_response})
        guardar_en_json(user_id, user_text, bot_response)
        return bot_response
    except Exception as e:
        return f"Error al generar respuesta: {str(e)}"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages"""
    print(f"Message received from ID: {update.message.chat_id}")
    handle_user_message(update.message)
    response = generate_response(update.message, pdf_index)

    # Divide la respuesta en fragmentos
    max_length = 4000
    if len(response) > max_length:
        parts = [response[i:i + max_length] for i in range(0, len(response), max_length)]
        for part in parts:
            await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
    else:
        await update.message.reply_text(response)


async def send_welcome_message(application):
    """Send a welcome message when the bot starts"""
    user_id = "7568207284"  # Replace with your ID
    welcome_message = ("¡Hola! 😊 Soy Prevencio-Bot, tu asistente de riesgos laborales. "
                       "Pregúntame lo que necesites sobre seguridad en PYMES.")
    await application.bot.send_message(chat_id=user_id, text=welcome_message)


def initialize_pdf_index():
    """Initialize the PDF index using Hugging Face embeddings and Gemini LLM"""
    global pdf_index
    if not os.path.exists(PDF_DIRECTORY):
        print(f"⚠️ Directory '{PDF_DIRECTORY}' does not exist.")
        return

    pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"⚠️ No PDFs found in '{PDF_DIRECTORY}'.")
        return

    print(f"📂 Found {len(pdf_files)} PDFs. Processing...")
    documents = []
    for file in pdf_files:
        file_path = os.path.join(PDF_DIRECTORY, file)
        text = extract_text_from_pdf(file_path)
        if text.strip():
            documents.append(Document(text=text))
            print(f"✅ Extracted text from '{file}' ({len(text)} characters).")
        else:
            print(f"⚠️ PDF '{file}' has no extractable text.")

    if not documents:
        print("❌ No text could be extracted from any PDF.")
        return

    try:
        # Configura el modelo de embeddings
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Configura el LLM como GoogleGenAI
        Settings.llm = GoogleGenAI(model="gemini-2.0-flash-lite", api_key=GOOGLE_API_KEY)
        pdf_index = VectorStoreIndex.from_documents(documents)
        print("✅ PDF index loaded successfully.")
    except Exception as e:
        print(f"❌ Error creating index: {str(e)}")


def main():
    global enlaces_disponibles
    initialize_pdf_index()

    # Cargar enlaces desde el archivo JSON
    try:
        with open("enlaces.json", "r", encoding="utf-8") as f:
            enlaces_disponibles = json.load(f)
        print(f"✅ Enlaces cargados: {len(enlaces_disponibles)} enlaces disponibles.")
    except Exception as e:
        print(f"❌ Error al cargar enlaces.json: {e}")

    bot = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(send_welcome_message) \
        .build()

    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("🤖 Bot is running...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()