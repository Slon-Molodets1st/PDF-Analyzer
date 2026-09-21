"""Функции для стриминга ответов агента"""

import asyncio
import streamlit as st
from typing import Dict, List, Any

async def stream_agent_response(agent, query: str):
    """
    Стримит ответ агента с событиями
    
    Args:
        agent: объект агента
        query: запрос пользователя
    
    Yields:
        dict: события агента
    """
    try:
        if agent is None:
            yield {"type": "error", "content": "❌ Агент не инициализирован"}
            return
        
        # Запуск агента с astream_events
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=query)]},
            version="v1"
        ):
            if event["event"] == "on_chat_model_stream":
                # Стриминг токенов
                content = event["data"]["chunk"].content
                if content:
                    yield {"type": "token", "content": content}
            
            elif event["event"] == "on_tool_start":
                # Начало выполнения инструмента
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                query_text = tool_input.get("query", str(tool_input))
                yield {
                    "type": "tool_start", 
                    "tool": tool_name,
                    "query": query_text
                }
            
            elif event["event"] == "on_tool_end":
                # Завершение выполнения инструмента
                tool_name = event["name"]
                output = event["data"].get("output", "")
                yield {
                    "type": "tool_end",
                    "tool": tool_name,
                    "output": str(output)[:500] + "..." if len(str(output)) > 500 else str(output)
                }
            
            elif event["event"] == "on_chain_start" and "agent" in event.get("name", ""):
                yield {"type": "thinking", "content": "🤔 Агент анализирует ваш вопрос..."}
            
            elif event["event"] == "on_chain_end" and event.get("name") == "agent":
                yield {"type": "done", "content": "✅ Агент завершил работу"}
    
    except Exception as e:
        yield {"type": "error", "content": f"❌ Ошибка: {str(e)}"}

def run_agent_with_progress(query: str, agent, progress_placeholder, status_placeholder, response_placeholder):
    """
    Запускает агента с отображением прогресса и стримингом
    
    Args:
        query: запрос пользователя
        agent: объект агента
        progress_placeholder: placeholder для прогресс-бара
        status_placeholder: placeholder для статуса
        response_placeholder: placeholder для ответа
    
    Returns:
        dict: результат работы агента
    """
    try:
        if agent is None:
            return {
                "answer": "❌ Агент не инициализирован",
                "tool_calls": [],
                "tool_results": []
            }
        
        status_placeholder.info("🚀 Запуск агента...")
        progress_placeholder.progress(0.1)
        
        # Создание контейнер для стриминга
        streaming_container = st.empty()
        full_response = ""
        tool_calls = []
        tool_results = []
        
        # Запуск асинхронного стриминга
        async def run_stream():
            nonlocal full_response, tool_calls, tool_results
            async for event in stream_agent_response(agent, query):
                if event["type"] == "token":
                    full_response += event["content"]
                    # Обновляем стриминг контейнер с маркером генерации
                    streaming_container.markdown(f"**📝 Генерация ответа:**\n\n{full_response}▌")
                    progress_placeholder.progress(0.3 + (len(full_response) % 10) * 0.05)
                
                elif event["type"] == "thinking":
                    status_placeholder.info(event["content"])
                    progress_placeholder.progress(0.2)
                
                elif event["type"] == "tool_start":
                    tool_calls.append({
                        "tool": event["tool"],
                        "query": event["query"]
                    })
                    status_placeholder.info(f"🔧 Использую инструмент: {event['tool']}...")
                    progress_placeholder.progress(0.4 + len(tool_calls) * 0.1)
                
                elif event["type"] == "tool_end":
                    tool_results.append({
                        "tool": event["tool"],
                        "result": event["output"]
                    })
                    status_placeholder.success(f"✅ Инструмент {event['tool']} завершил работу")
                    progress_placeholder.progress(0.5 + len(tool_results) * 0.1)
                
                elif event["type"] == "done":
                    status_placeholder.success("✅ Агент завершил работу!")
                    progress_placeholder.progress(1.0)
                
                elif event["type"] == "error":
                    status_placeholder.error(event["content"])
                    return {"error": event["content"]}
            
            return {"success": True}
        
        result = asyncio.run(run_stream())
        
        if result and "error" in result:
            return {
                "answer": result["error"],
                "tool_calls": tool_calls,
                "tool_results": tool_results
            }
        
        streaming_container.markdown(f"**📝 Ответ агента:**\n\n{full_response}")
        
        with response_placeholder:
            if tool_calls:
                st.subheader("🔧 Использованные инструменты:")
                for tool_call in tool_calls:
                    st.info(f"📌 Использован инструмент: **{tool_call['tool']}** с запросом: {tool_call['query']}")
            
            if tool_results:
                st.subheader("📊 Результаты работы инструментов:")
                for tool_result in tool_results:
                    with st.expander(f"📌 Результат от {tool_result['tool']}"):
                        st.markdown(tool_result['result'])
        
        return {
            "answer": full_response or "Агент не смог сгенерировать ответ.",
            "tool_calls": tool_calls,
            "tool_results": tool_results
        }
        
    except Exception as e:
        return {
            "answer": f"❌ Ошибка при работе агента: {str(e)}",
            "tool_calls": [],
            "tool_results": []
        }
