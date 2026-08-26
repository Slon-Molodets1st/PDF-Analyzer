from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
import uuid

def get_embeddings():
    """Настройка эмбеддингов"""
    return OllamaEmbeddings(
        model="all-minilm",
        base_url="http://localhost:11434"
    )

def get_llm(temperature: float = 0.1):
    """Настройка LLM"""
    return ChatOllama(
        model="llama3.2",
        temperature=temperature,
        base_url="http://localhost:11434"
    )

def create_vectorstore(chunks, embeddings):
    """Создание векторного хранилища"""
    session_id = str(uuid.uuid4())[:8]
    chroma_path = f"./chroma_db_{session_id}"
    
    vectorstore = Chroma.from_documents(
        chunks, 
        embeddings,
        persist_directory=chroma_path
    )
    
    return vectorstore, chroma_path
