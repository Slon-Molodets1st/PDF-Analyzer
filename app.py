import streamlit as st
from src.core.document_processor import process_pdf
from src.core.llm_config import get_llm
from src.chains.qa_chain import create_qa_chain
from src.chains.extraction_chain import create_extraction_chain
from src.chains.contradiction_chain import create_contradiction_chain
from src.agent.agent_builder import create_agent
from src.agent.streaming import run_agent_with_progress
from src.utils.file_utils import cleanup_temp_file

# Импорты для страницы
from src.models.contract_schema import ContractSchema
import os

st.set_page_config(page_title="Анализ контрактов", layout="wide")
st.title("📄 Чат с PDF")

# Инициализация session_state
def init_session_state():
    if 'retriever' not in st.session_state:
        st.session_state.retriever = None
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'tmp_file_path' not in st.session_state:
        st.session_state.tmp_file_path = None
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None

init_session_state()

# Создание вкладок
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Чат с документом", 
    "🔍 Извлечение сущностей", 
    "🔄 Поиск противоречий", 
    "🤖 Агент"
])

uploaded_file = st.file_uploader("Загрузите PDF", type="pdf")

if uploaded_file:
    tmp_path = None
    try:
        # Обработка PDF
        with st.spinner("Обработка PDF..."):
            tmp_path, docs, full_text, logical_blocks = process_pdf(uploaded_file)
            st.session_state.tmp_file_path = tmp_path
        
        # Настройка LLM и векторизация
        llm = get_llm()
        vectorstore, retriever = create_vectorstore(docs)
        st.session_state.retriever = retriever
        st.session_state.vectorstore = vectorstore
        
        # Создание цепей
        qa_chain = create_qa_chain(retriever, llm)
        extraction_chain = create_extraction_chain(llm)
        contradiction_chain = create_contradiction_chain(llm)
        
        # Создание агента
        agent = create_agent(retriever, llm)
        st.session_state.agent = agent
        st.session_state.agent_initialized = True
        
        st.success("✅ Все компоненты успешно инициализированы!")
        
        # --- Вкладки ---
        render_qa_tab(tab1, qa_chain, retriever)
        render_extraction_tab(tab2, extraction_chain, full_text)
        render_contradiction_tab(tab3, contradiction_chain, logical_blocks)
        render_agent_tab(tab4)
        
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")
    finally:
        cleanup_temp_file(tmp_path)
else:
    render_info_section()

# Функции рендеринга вкладок (вынесены в отдельные функции)
def render_qa_tab(tab, qa_chain, retriever):
    with tab:
        query = st.text_input("Задайте вопрос о документе:")
        if query:
            with st.spinner("Думаю..."):
                result = qa_chain.invoke(query)
                st.write("**Ответ:**", result)

def render_extraction_tab(tab, extraction_chain, full_text):
    with tab:
        st.subheader("📊 Структурированный анализ контракта")
        if st.button("🔍 Извлечь сущности", type="primary"):
st.subheader("📊 Структурированный анализ контракта")
        st.info("Нажмите кнопку ниже, чтобы извлечь ключевую информацию из документа")
        
        if st.button("🔍 Извлечь сущности", type="primary"):
            with st.spinner("Анализирую документ..."):
                try:
                    result = extraction_chain.invoke({
                        "text": full_text[:8000],
                        "format_instructions": """
                        Извлеки информацию и верни JSON с полями:
                        - company_name (строка)
                        - total_amount (целое число)
                        - signing_date (строка в формате ДД.ММ.ГГГГ)
                        - risks (массив строк, минимум 3 пункта)
                        - additional_terms (массив строк, опционально)
                        """
                    })
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("🏢 Компания", result.company_name)
                        st.metric("💰 Сумма контракта", f"{result.total_amount:,} ₽")
                        st.metric("📅 Дата подписания", result.signing_date)
                    
                    with col2:
                        st.subheader("⚠️ Риски")
                        for i, risk in enumerate(result.risks, 1):
                            st.warning(f"{i}. {risk}")
                        
                        if result.additional_terms:
                            st.subheader("📌 Дополнительные условия")
                            for term in result.additional_terms:
                                st.info(f"• {term}")
                    
                    with st.expander("📄 Показать JSON"):
                        json_data = result.model_dump()
                        st.json(json_data)
                        
                        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                        st.download_button(
                            label="💾 Скачать JSON",
                            data=json_str,
                            file_name="contract_analysis.json",
                            mime="application/json"
                        )
                        
                except Exception as e:
                    st.error(f"Ошибка при извлечении сущностей: {str(e)}")
                    st.info("Попробуйте использовать другую модель или проверьте формат документа")
  
def render_contradiction_tab(tab, contradiction_chain, logical_blocks):
    with tab:
        st.subheader("🔄 Поиск противоречий в документе")
        st.info("""
        **Как это работает:**
        1. Документ разбивается на логические блоки
        2. Каждый блок анализируется последовательно
        3. Используется память для запоминания предыдущих выводов
        4. Выявляются противоречия между блоками
        """)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            analyze_contradictions = st.button(
                "🔍 Начать поиск противоречий", 
                type="primary", 
                use_container_width=True
            )
        
        with col2:
            blocks_count = st.number_input(
                "Количество блоков",
                min_value=3,
                max_value=20,
                value=min(10, len(logical_blocks)),
                step=1
            )
        
        if analyze_contradictions:
            st.divider()
            st.write("### 📊 Результаты анализа")
            
            try:
                blocks_to_analyze = logical_blocks[:blocks_count]
                
                with st.spinner("Анализирую документ на противоречия..."):
                    results_container = st.container()
                    
                    analysis_results = find_contradictions(blocks_to_analyze)
                    
                    with results_container:
                        st.subheader("📋 Пошаговый анализ блоков")
                        
                        for result in analysis_results:
                            with st.expander(f"📄 Блок {result['block_number']}"):
                                st.write("**Фрагмент текста:**")
                                st.text(result['text_preview'])
                                
                                st.write("**Анализ:**")
                                st.write(result['analysis'])
                    
                    with st.spinner("Создаю итоговый отчет..."):
                        final_summary = summarize_contradictions(analysis_results)
                        
                        st.divider()
                        st.subheader("📊 Итоговый отчет о противоречиях")
                        
                        st.markdown("---")
                        st.markdown(final_summary)
                        st.markdown("---")
                        
                        st.download_button(
                            label="💾 Скачать отчет о противоречиях",
                            data=final_summary,
                            file_name="contradictions_report.txt",
                            mime="text/plain"
                        )
                    
                    st.success("✅ Анализ завершен!")
                    
            except Exception as e:
                st.error(f"Ошибка при поиске противоречий: {str(e)}")
                st.info("Попробуйте уменьшить количество блоков или использовать другой документ.")

def render_agent_tab(tab):
    with tab:
        st.subheader("🤖 Умный агент с доступом к документам и интернету")
        st.info("""
        **Как работает агент:**
        1. 🤔 Анализирует ваш вопрос
        2. 📄 Сначала ищет ответ в PDF документе
        3. 🌐 Если в PDF нет информации - ищет в интернете
        4. 📊 Сравнивает информацию из разных источников
        5. 💡 Дает комплексный ответ
        """)
        
        if st.session_state.agent_initialized and st.session_state.agent is not None:
            query = st.text_area("Задайте вопрос агенту:", height=100, 
                                placeholder="Например: Какая компания указана в контракте? Или найди в интернете информацию о похожих контрактах")
            
            if st.button("🤖 Спросить агента", type="primary", use_container_width=True):
                if query:
                    # Создаем контейнеры для прогресса и результатов
                    progress_container = st.container()
                    status_container = st.container()
                    response_container = st.container()
                    
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    with st.spinner("Агент работает над вашим запросом..."):
                        try:
                            # Запускаем агента с прогрессом и стримингом
                            result = run_agent_with_progress(
                                query, 
                                progress_bar, 
                                status_text,
                                response_container
                            )
                            
                            # Показываем финальный ответ и кнопку скачивания
                            if result["answer"]:
                                st.markdown("---")
                                st.subheader("💡 Полный ответ агента:")
                                st.markdown(result["answer"])
                                st.markdown("---")
                                
                                st.download_button(
                                    label="💾 Скачать ответ агента",
                                    data=result["answer"],
                                    file_name="agent_response.txt",
                                    mime="text/plain"
                                )
                                
                        except Exception as e:
                            st.error(f"❌ Ошибка при работе агента: {str(e)}")
                            st.info("Попробуйте переформулировать вопрос.")
                else:
                    st.warning("⚠️ Пожалуйста, введите вопрос.")
        else:
            st.warning("⚠️ Агент не инициализирован. Пожалуйста, загрузите PDF файл и дождитесь его обработки.")

def render_info_section():
    st.info("👆 Загрузите PDF-файл для начала работы")
    with st.expander("ℹ️ Как это работает"):
        with st.expander("ℹ️ Как это работает"):
        st.markdown("""
        **Четыре основные функции:**
        
        1. **💬 Чат с документом** - задавайте любые вопросы о содержимом PDF
        2. **🔍 Извлечение сущностей** - автоматический анализ контрактов:
           - Название компании
           - Сумма контракта
           - Дата подписания
           - Юридические риски
           - Дополнительные условия
        
        3. **🔄 Поиск противоречий** - сложная цепочка анализа:
           - Разбивка на логические блоки
           - Последовательный анализ с памятью
           - Выявление противоречий между блоками
           - Создание итогового отчета
        
        4. **🤖 Агент** - умный помощник с доступом к инструментам:
           - Поиск в PDF документе
           - Поиск в интернете
           - Сравнение информации из разных источников
           - Самостоятельное принятие решений о том, какой инструмент использовать
        
        **Технологии:** LangChain, LangGraph, Ollama (Llama 3.2), ChromaDB, Pydantic
        """)
