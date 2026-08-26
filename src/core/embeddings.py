"""Настройка эмбеддингов для векторного поиска"""

from langchain_ollama import OllamaEmbeddings
import os

def get_embeddings(model: str = "all-minilm", base_url: str = "http://localhost:11434"):
    """
    Создает и возвращает объект эмбеддингов Ollama
    
    Args:
        model: название модели эмбеддингов
        base_url: URL сервера Ollama
    
    Returns:
        OllamaEmbeddings: объект эмбеддингов
    """
    # Можно переопределить через переменные окружения
    model = os.getenv("EMBEDDING_MODEL", model)
    base_url = os.getenv("OLLAMA_BASE_URL", base_url)
    
    return OllamaEmbeddings(
        model=model,
        base_url=base_url
    )
