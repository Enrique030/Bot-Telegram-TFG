import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from telegram import Message
from telegram.constants import ParseMode

from src.bot_chat_gemini import (
    guardar_en_json,
    handle_user_message,
    extract_text_from_pdf,
    get_web_links,
    generate_response,
    initialize_pdf_index,
    message_handler,
    mensajes,
)

class TestBot(unittest.IsolatedAsyncioTestCase):

    # --- Tests de funciones puras ---

    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    @patch("os.path.exists", return_value=True)
    def test_guardar_en_json(self, mock_exists, mock_file):
        guardar_en_json("1", "Hola", "Respuesta")
        mock_file.assert_called_with("conversaciones.json", "w", encoding="utf-8")

    def test_handle_user_message(self):
        mensajes.clear()
        mock_msg = MagicMock()
        mock_msg.from_user.id = 123
        mock_msg.text = "Mensaje de prueba"
        handle_user_message(mock_msg)
        self.assertIn(123, mensajes)
        self.assertEqual(mensajes[123]["messages"][0]["content"], "Mensaje de prueba")

    @patch("PyPDF2.PdfReader")
    def test_extract_text_from_pdf(self, mock_reader):
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Texto PDF"
        mock_reader.return_value = mock_pdf

        with patch("builtins.open", mock_open(read_data="data")):
            texto = extract_text_from_pdf("archivo.pdf")
            self.assertIn("Texto PDF", texto)

    @patch("requests.get")
    def test_get_web_links(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "organic_results": [
                {"title": "Título 1", "link": "https://ejemplo.com/1"},
                {"title": "Título 2", "link": "https://ejemplo.com/2"},
            ]
        }
        mock_get.return_value = mock_response
        links = get_web_links("riesgos", "clave_api", 2)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0][0], "Título 1")

    # --- Tests de Gemini, PDFs y Telegram ---

    @patch("src.bot_chat_gemini.query_pdf_index", return_value="Texto índice")
    @patch("src.bot_chat_gemini.get_web_links", return_value=[("Link A", "https://a.com")])
    @patch("src.bot_chat_gemini.genai.GenerativeModel")
    def test_generate_response(self, mock_model_class, mock_get_links, mock_query_index):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Respuesta generada"
        mock_model_class.return_value = mock_model

        mock_msg = MagicMock()
        mock_msg.from_user.id = 42
        mock_msg.text = "riesgos laborales"
        mensajes.clear()

        respuesta = generate_response(mock_msg, MagicMock())
        self.assertIn("Respuesta generada", respuesta)
        self.assertIn("https://a.com", respuesta)

    '''
    @patch("src.bot_chat_gemini.VectorStoreIndex.from_documents")
    @patch("src.bot_chat_gemini.Document")
    @patch("src.bot_chat_gemini.extract_text_from_pdf", return_value="Texto simulado")
    @patch("os.listdir", return_value=["doc1.pdf"])
    @patch("os.path.exists", return_value=True)
    @patch("src.bot_chat_gemini.Settings")
    def test_initialize_pdf_index(
            self,
            mock_settings,
            mock_exists,
            mock_listdir,
            mock_extract,
            mock_document,
            mock_from_documents
    ):

        mock_instance = MagicMock()
        mock_from_documents.return_value = mock_instance

        initialize_pdf_index()

        mock_from_documents.assert_called_once()
        mock_document.assert_called_once_with(text="Texto simulado")
    '''

    @patch("src.bot_chat_gemini.generate_response", return_value="Texto respuesta")
    @patch("src.bot_chat_gemini.handle_user_message")
    async def test_message_handler(self, mock_handle, mock_generate):
        mock_msg = MagicMock(spec=Message)
        mock_msg.chat_id = 42
        mock_msg.text = "Hola"
        mock_msg.reply_text = AsyncMock()
        mock_update = MagicMock()
        mock_update.message = mock_msg

        mock_context = MagicMock()

        await message_handler(mock_update, mock_context)
        mock_generate.assert_called_once()
        mock_msg.reply_text.assert_awaited_with(
            "Texto respuesta", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False
        )

if __name__ == "__main__":
    unittest.main()
