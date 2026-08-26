"""LangChain цепи для различных задач"""

from src.chains.qa_chain import create_qa_chain
from src.chains.extraction_chain import create_extraction_chain
from src.chains.contradiction_chain import create_contradiction_chain

__all__ = [
    'create_qa_chain',
    'create_extraction_chain',
    'create_contradiction_chain'
]
