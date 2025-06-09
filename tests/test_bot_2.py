import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from telegram import Message
from telegram.constants import ParseMode

# Importa funciones después del patch de JSON_FILE si es necesario
import src.bot_chat_gemini as bot

class TestBot(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Crear un archivo JSON temporal
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_json_path = os.path.join(self.temp_dir.name, "test_conversaciones.json")

        # Parchear la variable JSON_FILE en el módulo original
        self.json_patch = patch.object(bot, "JSON_FILE", self.temp_json_path)
        self.json_patch.start()

    def tearDown(self):
        # Detener el parcheo y limpiar temporales
        self.json_patch.stop()
        self.temp_dir.cleanup()

    def test_guardar_en_json(self):
        bot.guardar_en_json("1", "Hola", "Respuesta")
        with open(self.temp_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn("1", data)
            self.assertEqual(data["1"][0]["usuario"], "Hola")
            self.assertEqual(data["1"][0]["bot"], "Respuesta")

    def test_handle_user_message(self):
        bot.mensajes.clear()
        mock_msg = MagicMock()
        mock_msg.from_user.id = 123
        mock_msg.text = "Mensaje de prueba"
        bot.handle_user_message(mock_msg)
        self.assertIn(123, bot.mensajes)
        self.assertEqual(bot.mensajes[123]["messages"][0]["content"], "Mensaje de prueba")

    @patch("PyPDF2.PdfReader")
    def test_extract_text_from_pdf(self, mock_reader):
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Texto PDF"
        mock_reader.return_value = mock_pdf

        with patch("builtins.open", mock_open(read_data="data")):
            texto = bot.extract_text_from_pdf("archivo.pdf")
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
        links = bot.get_web_links("riesgos", "clave_api", 2)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0][0], "Título 1")

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
        bot.mensajes.clear()

        respuesta = bot.generate_response(mock_msg, MagicMock())
        self.assertIn("Respuesta generada", respuesta)
        self.assertIn("https://a.com", respuesta)

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

        await bot.message_handler(mock_update, mock_context)
        mock_generate.assert_called_once()
        mock_msg.reply_text.assert_awaited_with(
            "Texto respuesta", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False
        )

if __name__ == "__main__":
    unittest.main()
