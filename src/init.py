"""
Contract Analyzer - приложение для анализа контрактов с использованием AI
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from src.core.document_processor import process_pdf
from src.core.llm_config import get_llm, get_embeddings
from src.chains.qa_chain import create_qa_chain
from src.chains.extraction_chain import create_extraction_chain

__all__ = [
    'process_pdf',
    'get_llm',
    'get_embeddings',
    'create_qa_chain',
    'create_extraction_chain'
]
