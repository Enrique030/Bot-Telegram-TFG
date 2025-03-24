
import os

from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader

app = Flask(__name__)

API_KEY = os.getenv("2ca92abc95432617d5b26f5f41fdeeb1b2e9677676b8270952d6bab1b867e523")

# 📌 1. Cargar modelo de lenguaje local
modelo_nombre = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(modelo_nombre)
modelo = AutoModelForCausalLM.from_pretrained(modelo_nombre, device_map="auto")
generador = pipeline("text-generation", model=modelo, tokenizer=tokenizer, max_new_tokens=200)


# Procesar documentos y crear base vectorial
def cargar_documentos():
    documentos = []
    for archivo in os.listdir("documentos"):
        if archivo.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join("documentos", archivo))
            documentos.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    textos = splitter.split_documents(documentos)

    return textos


def crear_base_vectorial():
    textos = cargar_documentos()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(textos, embeddings)
    return vectorstore


vectorstore = crear_base_vectorial()
retriever = vectorstore.as_retriever()
qa_chain = RetrievalQA.from_chain_type(llm=generador, retriever=retriever, chain_type="stuff")


# API para responder preguntas
@app.route('/procesar', methods=['POST'])
def procesar():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "Acceso no autorizado"}), 403

    data = request.get_json()
    if not data or 'consulta' not in data:
        return jsonify({'error': 'No se ha proporcionado la consulta'}), 400

    consulta = data['consulta']
    respuesta = qa_chain.run(consulta)

    return jsonify({'respuesta': respuesta})


if __name__ == '__main__':
    app.run(host='localhost', port=5000, ssl_context=('cert.pem', 'key.pem'))
