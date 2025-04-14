import os
import PyPDF2
import requests
import json
from llama_index.core import VectorStoreIndex, Document
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
JSON_FILE = "conversaciones.json"
PDF_DIRECTORY = "documentos"

# Store user messages
mensajes = {}

# Initialize the document index as None
pdf_index = None

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
    """Generate response using Mistral AI and PDF index"""
    user_id = message.from_user.id
    user_text = message.text

    if user_id not in mensajes:
        mensajes[user_id] = {"messages": []}

    mensajes[user_id]["messages"].append({"role": "user", "content": user_text})

    if pdf_index and any(keyword in user_text.lower() for keyword in ["riesgos", "laboral", "pymes", "seguridad"]):
        info_rag = query_pdf_index(pdf_index, user_text)
        context_message = f"Información adicional de documentos: {info_rag}"
        mensajes[user_id]["messages"].append({"role": "system", "content": context_message})

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-tiny",
        "messages": mensajes[user_id]["messages"]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        bot_response = response.json()["choices"][0]["message"]["content"]
        mensajes[user_id]["messages"].append({"role": "assistant", "content": bot_response})
        guardar_en_json(user_id, user_text, bot_response)
        return bot_response
    except Exception as e:
        return f"Error al generar respuesta: {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages"""
    print(f"Mensaje recibido de ID: {update.message.chat_id}")
    handle_user_message(update.message)
    response = generate_response(update.message, pdf_index)
    await update.message.reply_text(response)

async def send_welcome_message(application):
    """Send a welcome message when the bot starts"""
    user_id = "7568207284"  # Replace with your ID
    welcome_message = ("¡Hola! 😊 Soy Prevencio-Bot, tu asistente de riesgos laborales. "
                       "Pregúntame lo que necesites sobre seguridad en PYMES.")
    await application.bot.send_message(chat_id=user_id, text=welcome_message)

def initialize_pdf_index():
    """Initialize the PDF index using Hugging Face embeddings"""
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
        # Use Hugging Face's sentence-transformers model
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        pdf_index = VectorStoreIndex.from_documents(documents)
        print("✅ PDF index loaded successfully.")
    except Exception as e:
        print(f"❌ Error creating index: {str(e)}")

def main():
    """Main function"""
    initialize_pdf_index()
    bot = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(send_welcome_message) \
        .build()

    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("🤖 Bot is running...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()