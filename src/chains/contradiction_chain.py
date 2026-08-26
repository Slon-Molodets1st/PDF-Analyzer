"""Цепь для поиска противоречий в документе"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.memory.simple_memory import SimpleMemory
from typing import List, Dict
import streamlit as st

CONTRADICTION_TEMPLATE = """
Ты - эксперт по анализу юридических документов. Твоя задача - найти противоречия в контракте.

Ранее найденные противоречия и выводы:
{memory_summary}

Текущий блок документа (Блок #{block_number}):
{current_block}

Проанализируй текущий блок на предмет противоречий с предыдущими блоками.
Удели особое внимание:
1. Финансовым показателям (суммы, сроки оплаты, штрафы)
2. Юридическим обязательствам (права и обязанности сторон)
3. Логике изложения (противоречащие утверждения)
4. Терминологии (разные определения одного и того же)

Если находишь противоречия, опиши их подробно. Если нет - просто подтверди, что блок согласован.
Опиши найденные противоречия в формате:
- Тип противоречия: [финансовое/юридическое/логическое/терминологическое]
- Что противоречит: [описание]
- Степень серьезности: [критическое/высокое/среднее/низкое]

Ответ:
"""

SUMMARY_TEMPLATE = """
Ты - эксперт по юридическому анализу. Создай итоговый отчет по найденным противоречиям.

Результаты анализа по блокам:
{analysis_results}

Создай структурированный отчет, который содержит:
1. Общее количество найденных противоречий
2. Категоризацию противоречий по типу
3. Оценку критичности каждого противоречия
4. Рекомендации по устранению противоречий

Ответ:
"""

class ContradictionChain:
    """Класс для управления цепью поиска противоречий"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(CONTRADICTION_TEMPLATE)
        self.summary_prompt = ChatPromptTemplate.from_template(SUMMARY_TEMPLATE)
    
    def find_contradictions(self, blocks: List, llm) -> List[Dict]:
        """
        Находит противоречия в блоках документа
        
        Args:
            blocks: список блоков документа
            llm: объект LLM
        
        Returns:
            List[Dict]: список результатов анализа
        """
        memory = SimpleMemory()
        analysis_results = []
        total_blocks = len(blocks)
        
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        for i, block in enumerate(blocks, 1):
            status_placeholder.info(f"🔍 Анализирую блок {i} из {total_blocks}...")
            progress_placeholder.progress(i / total_blocks)
            
            memory_vars = memory.load_memory_variables()
            memory_summary = memory_vars.get("memory_summary", "Нет предыдущих блоков.")
            
            chain = (
                {
                    "memory_summary": lambda x: memory_summary,
                    "block_number": lambda x: i,
                    "current_block": lambda x: block.page_content[:3000]
                }
                | self.prompt
                | llm
                | StrOutputParser()
            )
            
            result = chain.invoke({})
            
            memory.save_context(
                {"block_number": i, "text_preview": block.page_content[:200]},
                result
            )
            
            analysis_results.append({
                'block_number': i,
                'analysis': result,
                'text_preview': block.page_content[:200] + "..."
            })
        
        progress_placeholder.empty()
        status_placeholder.empty()
        
        return analysis_results
    
    def summarize_contradictions(self, analysis_results: List[Dict], llm) -> str:
        """
        Создает итоговый отчет по найденным противоречиям
        
        Args:
            analysis_results: результаты анализа блоков
            llm: объект LLM
        
        Returns:
            str: итоговый отчет
        """
        formatted_results = "\n\n".join([
            f"Блок {r['block_number']}: {r['analysis']}" 
            for r in analysis_results
        ])
        
        chain = self.summary_prompt | llm | StrOutputParser()
        return chain.invoke({"analysis_results": formatted_results})

def create_contradiction_chain(llm) -> ContradictionChain:
    """
    Создает цепь для поиска противоречий
    
    Args:
        llm: объект LLM
    
    Returns:
        ContradictionChain: объект цепи
    """
    return ContradictionChain(llm)
