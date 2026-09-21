"""Функции для поиска в интернете"""

import os
from typing import Optional

def google_search(query: str) -> str:
    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",      
            max_results=5,
            include_answer=True,       
            include_raw_content=False 
        )
        
        formatted_results = []
        
        if response.get('answer'):
            formatted_results.append(f"💡 Краткий ответ: {response['answer']}\n")
        
        for i, result in enumerate(response.get('results', []), 1):
            title = result.get('title', 'Без названия')
            content = result.get('content', '')
            url = result.get('url', '')
            score = result.get('score', 0)
            formatted_results.append(
                f"📌 РЕЗУЛЬТАТ {i}:\n"
                f"Название: {title}\n"
                f"Содержание: {content}\n"
                f"Ссылка: {url}\n"
                f"Релевантность: {score:.2f}\n"
            )
        
        return "\n".join(formatted_results) if formatted_results else "Ничего не найдено."
        
    except Exception as e:
        return f"❌ Ошибка при поиске: {str(e)}"

def tavily_search(query: str, api_key: Optional[str] = None) -> str:
    """
    Реализация поиска через Tavily API (если нужен реальный поиск)
    
    Args:
        query: поисковый запрос
        api_key: API ключ Tavily
    
    Returns:
        str: результаты поиска
    """
    try:
        from tavily import TavilyClient
        
        api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "❌ API ключ Tavily не найден"
        
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="advanced")
        
        results = []
        for result in response.get("results", [])[:5]:
            results.append(f"""
📌 {result.get('title', 'Без названия')}
{result.get('content', 'Нет содержания')}
Источник: {result.get('url', 'Нет URL')}
""")
        
        return "\n".join(results) if results else "❌ Ничего не найдено"
    except Exception as e:
        return f"❌ Ошибка при поиске через Tavily: {str(e)}"
