from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from src.agent.tools import get_all_tools

def create_agent(retriever, llm):
    """Создает агента с инструментами"""
    tools = get_all_tools(retriever)
    llm_with_tools = llm.bind_tools(tools)
    
    def call_model(state: MessagesState):
        messages = state["messages"]
        system_message = SystemMessage(content="""
        Ты - умный ассистент, который помогает анализировать документы.
        Используй инструменты для поиска информации.
        Всегда объясняй, какой инструмент используешь и почему.
        """)
        response = llm_with_tools.invoke([system_message] + messages)
        return {"messages": [response]}
    
    # Создание графа
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        lambda state: "tools" if state["messages"][-1].tool_calls else END
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
