import os
import PyPDF2
import google.generativeai as genai
import json
import requests
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
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # Nueva variable para la API de SerpAPI
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

def get_web_links(query, api_key, num_links=2):
    """Fetch dynamic web links using SerpAPI"""
    endpoint = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "num": num_links,
        "hl": "es",  # Resultados en español
        "gl": "es"   # Región España
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        search_results = response.json()
        links = [(result["title"], result["link"]) for result in search_results.get("organic_results", [])]
        return links[:num_links]
    except Exception as e:
        print(f"Error fetching web links: {e}")
        return []

def generate_response(message, pdf_index):
    """Generate response using Gemini with concise answers, contextual links, and dynamic web links"""
    user_id = message.from_user.id
    user_text = message.text.lower()

    if user_id not in mensajes:
        mensajes[user_id] = {"messages": []}

    mensajes[user_id]["messages"].append({"role": "user", "content": user_text})

    # Determine if the query requires information from the index
    context = ""
    keywords = [
        "riesgos", "laboral", "laborales", "prevención", "seguridad", "salud", "trabajo",
        "normativa", "ley", "decreto", "reglamento", "31/1995", "PYME"
    ]
    if pdf_index and any(keyword in user_text for keyword in keywords):
        info_rag = query_pdf_index(pdf_index, user_text)
        context = f"Información adicional de documentos: {info_rag}\n\n"

    # Build conversation history
    conversation_history = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in mensajes[user_id]["messages"]]
    )

    # Prepare list of available links for the prompt
    enlaces_texto = "\n".join([f"- {nombre}: {url}" for nombre, url in enlaces_disponibles.items()])

    # Adjusted prompt to include links in Markdown format
    prompt = (
        f"{context}Historia de la conversación:\n{conversation_history}\n\n"
        f"Responde como un consultor experto en riesgos laborales. Sé claro, conciso y responde SOLO a lo preguntado. "
        f"Usa un tono técnico si la pregunta lo requiere. Si la respuesta se refiere a normativas, leyes o guías específicas, "
        f"incluye enlaces relevantes de esta lista:\n{enlaces_texto}\n\n"
        f"Limita la respuesta a 100-150 palabras. Devuélveme SOLO texto plano, si necesitas enumerar una lista usa guiones (-). "
        f"Evita el formato Markdown con **Palabras**. Cuando incluyas un enlace, usa el formato Markdown: [Nombre](URL)."
    )

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        bot_response = response.text.strip()

        # Clean any residual formatting
        bot_response = bot_response.replace("*", "")

        # Add dynamic web links using SerpAPI
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
        return f"Error al generar respuesta: {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages"""
    print(f"Message received from ID: {update.message.chat_id}")
    handle_user_message(update.message)
    response = generate_response(update.message, pdf_index)

    # Split the response into chunks if necessary
    max_length = 4000
    if len(response) > max_length:
        parts = [response[i:i + max_length] for i in range(0, len(response), max_length)]
        for part in parts:
            await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
    else:
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)

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
        # Configure embedding model
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Configure LLM as GoogleGenAI
        Settings.llm = GoogleGenAI(model="gemini-2.0-flash-lite", api_key=GOOGLE_API_KEY)
        pdf_index = VectorStoreIndex.from_documents(documents)
        print("✅ PDF index loaded successfully.")
    except Exception as e:
        print(f"❌ Error creating index: {str(e)}")

def main():
    global enlaces_disponibles
    initialize_pdf_index()

    # Load links from JSON file
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