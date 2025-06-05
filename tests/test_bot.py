
import unittest
from unittest.mock import patch, mock_open, MagicMock
# import os
# import json

# python -m unittest tests/test_bot.py


# Importar funciones desde el archivo original
from src.bot_chat_gemini import (
    guardar_en_json,
    handle_user_message,
    extract_text_from_pdf,
    get_web_links,
)

class TestBotFunctions(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    @patch("os.path.exists", return_value=True)
    def test_guardar_en_json_nuevo_usuario(self, mock_exists, mock_file):
        guardar_en_json("123", "Hola", "Respuesta")
        mock_file.assert_called_with("conversaciones.json", "w", encoding="utf-8")

    def test_handle_user_message_crea_entrada(self):
        from src.bot_chat_gemini import mensajes
        mensajes.clear()
        mock_msg = MagicMock()
        mock_msg.from_user.id = 123
        mock_msg.text = "Hola mundo"
        handle_user_message(mock_msg)
        self.assertIn(123, mensajes)
        self.assertEqual(mensajes[123]["messages"][0]["content"], "Hola mundo")

    @patch("PyPDF2.PdfReader")
    def test_extract_text_from_pdf(self, mock_reader):
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Contenido PDF"
        mock_reader.return_value = mock_pdf

        with patch("builtins.open", mock_open(read_data="data")):
            text = extract_text_from_pdf("dummy.pdf")
            self.assertIn("Contenido PDF", text)

    @patch("requests.get")
    def test_get_web_links(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "organic_results": [
                {"title": "Título 1", "link": "https://example.com/1"},
                {"title": "Título 2", "link": "https://example.com/2"},
            ]
        }
        mock_get.return_value = mock_resp
        results = get_web_links("prevención", "fake_api", 2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], "Título 1")

if __name__ == "__main__":
    unittest.main()
