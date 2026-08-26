import tempfile
import os
from typing import Tuple, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

def process_pdf(uploaded_file) -> Tuple[str, List[Document], str, List[Document]]:
    """Загружает и обрабатывает PDF файл"""
    # Сохраняем загруженный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    # Загружаем PDF
    loader = PyPDFLoader(tmp_path)
    docs = loader.load()
    
    # Собираем полный текст
    full_text = "\n\n".join([doc.page_content for doc in docs])
    
    # Создаем сплиттеры
    chat_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    chunks = chat_splitter.split_documents(docs)
    
    contradiction_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=300,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    logical_blocks = contradiction_splitter.split_documents(docs)
    
    return tmp_path, chunks, full_text, logical_blocks
