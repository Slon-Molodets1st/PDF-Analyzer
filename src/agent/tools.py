from langchain_core.tools import tool
from src.agent.web_search import google_search

def create_pdf_search_tool(retriever):
    """Создает инструмент поиска в PDF"""
    @tool
    def pdf_search_tool(query: str) -> str:
        """Используйте этот инструмент для поиска информации в загруженном PDF документе"""
        try:
            if retriever is None:
                return "❌ PDF документ не загружен или не обработан."
            
            docs = retriever.invoke(query)
            if not docs:
                return "❌ В PDF документе не найдено информации по вашему запросу."
            
            results = []
            for i, doc in enumerate(docs[:3], 1):
                results.append(f"📄 Результат {i} из PDF:\n{doc.page_content[:500]}")
            
            return "\n\n".join(results)
        except Exception as e:
            return f"❌ Ошибка при поиске в PDF: {str(e)}"
    
    return pdf_search_tool

@tool
def web_search_tool(query: str) -> str:
    """Используйте этот инструмент для поиска актуальной информации в интернете"""
    return google_search(query)

def get_all_tools(retriever):
    """Возвращает все доступные инструменты"""
    return [create_pdf_search_tool(retriever), web_search_tool]
