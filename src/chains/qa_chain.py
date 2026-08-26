from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def create_qa_chain(retriever, llm):
    """Создает цепь для ответов на вопросы"""
    template = """Вы помощник, который отвечает на вопросы на основе предоставленного контекста.
    Используйте только информацию из контекста для ответа.
    Если в контексте нет ответа, скажите, что не знаете.
    
    Контекст: {context}
    
    Вопрос: {question}
    
    Ответ:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    qa_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return qa_chain
