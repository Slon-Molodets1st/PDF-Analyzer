"""
Главный файл приложения Streamlit для анализа контрактов
"""

import streamlit as st
import os
from src.core.document_processor import process_pdf
from src.core.llm_config import get_llm, create_vectorstore
from src.chains.qa_chain import create_qa_chain
from src.chains.extraction_chain import create_extraction_chain
from src.chains.contradiction_chain import create_contradiction_chain
from src.agent.agent_builder import create_agent
from src.agent.streaming import run_agent_with_progress
from src.utils.file_utils import cleanup_temp_file, cleanup_chroma_db

# Настройка страницы
st.set_page_config(
    page_title="Анализ контрактов",
    page_icon="📄",
    layout="wide"
)

# CSS для улучшения внешнего вида
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
    }
    .reportview-container .markdown-text-container {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Заголовок
st.title("📄 Чат с PDF")

# Инициализация session_state
def init_session_state():
    """Инициализирует все переменные в session_state"""
    defaults = {
        'retriever': None,
        'agent_initialized': False,
        'agent': None,
        'tmp_file_path': None,
        'vectorstore': None,
        'chroma_path': None,
        'qa_chain': None,
        'extraction_chain': None,
        'contradiction_chain': None,
        'full_text': None,
        'logical_blocks': None,
        'chunks': None,
        'llm': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Создание вкладок
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Чат с документом", 
    "🔍 Извлечение сущностей", 
    "🔄 Поиск противоречий", 
    "🤖 Агент"
])

# Загрузка файла
uploaded_file = st.file_uploader(
    "Загрузите PDF файл для анализа",
    type="pdf",
    help="Поддерживаются файлы в формате PDF"
)

# Обработка загруженного файла
if uploaded_file:
    # Проверяем, нужно ли обрабатывать новый файл
    if st.session_state.tmp_file_path is None:
        tmp_path = None
        try:
            with st.spinner("🔄 Обработка PDF файла..."):
                # Обработка PDF
                tmp_path, chunks, full_text, logical_blocks = process_pdf(uploaded_file)
                st.session_state.tmp_file_path = tmp_path
                st.session_state.chunks = chunks
                st.session_state.full_text = full_text
                st.session_state.logical_blocks = logical_blocks
                
                # Настройка LLM
                llm = get_llm()
                st.session_state.llm = llm
                
                # Создание векторного хранилища
                vectorstore, chroma_path = create_vectorstore(chunks, get_embeddings())
                st.session_state.vectorstore = vectorstore
                st.session_state.chroma_path = chroma_path
                retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
                st.session_state.retriever = retriever
                
                # Создание цепей
                st.session_state.qa_chain = create_qa_chain(retriever, llm)
                st.session_state.extraction_chain = create_extraction_chain(llm)
                st.session_state.contradiction_chain = create_contradiction_chain(llm)
                
                # Создание агента
                agent = create_agent(retriever, llm)
                st.session_state.agent = agent
                st.session_state.agent_initialized = True
                
            st.success("✅ Все компоненты успешно инициализированы!")
            
        except Exception as e:
            st.error(f"❌ Ошибка при обработке PDF: {str(e)}")
            st.info("Попробуйте перезагрузить приложение и загрузить файл снова.")
            if tmp_path:
                cleanup_temp_file(tmp_path)
    
 
    render_qa_tab(tab1)
 
    render_extraction_tab(tab2)
    
    render_contradiction_tab(tab3)
  
    render_agent_tab(tab4)

else:
    render_info_section()


def render_qa_tab(tab):
    """Рендерит вкладку чата"""
    with tab:
        st.subheader("💬 Задайте вопрос о документе")
        st.markdown("---")
        
        query = st.text_input(
            "Введите ваш вопрос:",
            placeholder="Например: Какие основные условия контракта?"
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            show_sources = st.checkbox("Показать источники", value=True)
        
        if query and st.session_state.qa_chain:
            with st.spinner("🤔 Думаю над ответом..."):
                try:
                    result = st.session_state.qa_chain.invoke(query)
                    
                    st.markdown("### 📝 Ответ:")
                    st.markdown(result)
                    
                    if show_sources:
                        with st.expander("📚 Показать источники", expanded=False):
                            source_docs = st.session_state.retriever.invoke(query)
                            for i, doc in enumerate(source_docs, 1):
                                st.markdown(f"**Источник {i}:**")
                                st.text(doc.page_content[:500] + "...")
                                st.markdown("---")
                            
                except Exception as e:
                    st.error(f"❌ Ошибка при генерации ответа: {str(e)}")

def render_extraction_tab(tab):
    """Рендерит вкладку извлечения сущностей"""
    with tab:
        st.subheader("📊 Структурированный анализ контракта")
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("""
            **Что будет извлечено:**
            - 🏢 Название компании
            - 💰 Сумма контракта
            - 📅 Дата подписания
            - ⚠️ Юридические риски
            - 📌 Дополнительные условия
            """)
        
        with col2:
            if st.button("🔍 Извлечь сущности", type="primary", use_container_width=True):
                if st.session_state.extraction_chain and st.session_state.full_text:
                    with st.spinner("🔬 Анализирую документ..."):
                        try:
                            result = st.session_state.extraction_chain.invoke({
                                "text": st.session_state.full_text[:8000]
                            })
                            
                            # Отображение результатов
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
                            
                            # JSON экспорт
                            with st.expander("📄 Показать JSON", expanded=False):
                                json_data = result.model_dump()
                                st.json(json_data)
                                
                                import json
                                json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                                st.download_button(
                                    label="💾 Скачать JSON",
                                    data=json_str,
                                    file_name="contract_analysis.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                                
                        except Exception as e:
                            st.error(f"❌ Ошибка при извлечении: {str(e)}")

def render_contradiction_tab(tab):
    """Рендерит вкладку поиска противоречий"""
    with tab:
        st.subheader("🔄 Поиск противоречий в документе")
        st.markdown("---")
        
        st.info("""
        **Как это работает:**
        1. 📄 Документ разбивается на логические блоки
        2. 🔍 Каждый блок анализируется последовательно
        3. 🧠 Используется память для запоминания предыдущих выводов
        4. ⚠️ Выявляются противоречия между блоками
        5. 📊 Создается итоговый отчет
        """)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            analyze_button = st.button(
                "🔍 Начать поиск противоречий", 
                type="primary", 
                use_container_width=True
            )
        
        with col2:
            if st.session_state.logical_blocks:
                blocks_count = st.number_input(
                    "Количество блоков",
                    min_value=3,
                    max_value=20,
                    value=min(10, len(st.session_state.logical_blocks)),
                    step=1
                )
            else:
                blocks_count = 10
        
        if analyze_button and st.session_state.contradiction_chain:
            if not st.session_state.logical_blocks:
                st.warning("⚠️ Документ не загружен или не обработан")
            else:
                st.divider()
                st.write("### 📊 Результаты анализа")
                
                try:
                    blocks_to_analyze = st.session_state.logical_blocks[:blocks_count]
                    
                    with st.spinner("🔍 Анализирую документ на противоречия..."):
                        # Анализ блоков
                        results_container = st.container()
                        analysis_results = st.session_state.contradiction_chain.find_contradictions(
                            blocks_to_analyze,
                            st.session_state.llm
                        )
                        
                        with results_container:
                            st.subheader("📋 Пошаговый анализ блоков")
                            
                            for result in analysis_results:
                                with st.expander(f"📄 Блок {result['block_number']}"):
                                    st.text("**Фрагмент текста:**")
                                    st.text(result['text_preview'])
                                    st.text("**Анализ:**")
                                    st.write(result['analysis'])
                        
                        # Итоговый отчет
                        with st.spinner("📊 Создаю итоговый отчет..."):
                            final_summary = st.session_state.contradiction_chain.summarize_contradictions(
                                analysis_results,
                                st.session_state.llm
                            )
                            
                            st.divider()
                            st.subheader("📊 Итоговый отчет о противоречиях")
                            st.markdown("---")
                            st.markdown(final_summary)
                            st.markdown("---")
                            
                            st.download_button(
                                label="💾 Скачать отчет о противоречиях",
                                data=final_summary,
                                file_name="contradictions_report.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                        st.success("✅ Анализ завершен!")
                        
                except Exception as e:
                    st.error(f"❌ Ошибка при поиске противоречий: {str(e)}")
                    st.info("Попробуйте уменьшить количество блоков или использовать другой документ.")

def render_agent_tab(tab):
    """Рендерит вкладку агента"""
    with tab:
        st.subheader("🤖 Умный агент с доступом к документам и интернету")
        st.markdown("---")
        
        st.info("""
        **Как работает агент:**
        1. 🤔 Анализирует ваш вопрос
        2. 📄 Сначала ищет ответ в PDF документе
        3. 🌐 Если в PDF нет информации - ищет в интернете
        4. 📊 Сравнивает информацию из разных источников
        5. 💡 Дает комплексный ответ с объяснениями
        """)
        
        if st.session_state.agent_initialized and st.session_state.agent is not None:
            query = st.text_area(
                "Задайте вопрос агенту:",
                height=100,
                placeholder="Например: Какая компания указана в контракте? Или найди в интернете информацию о похожих контрактах"
            )
            
            if st.button("🤖 Спросить агента", type="primary", use_container_width=True):
                if query:
                    # Контейнеры для прогресса и результатов
                    progress_container = st.container()
                    status_container = st.container()
                    response_container = st.container()
                    
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    with st.spinner("🤖 Агент работает над вашим запросом..."):
                        try:
                            # Запуск агента с прогрессом и стримингом
                            result = run_agent_with_progress(
                                query,
                                st.session_state.agent,
                                progress_bar,
                                status_text,
                                response_container
                            )
                            
                            # Финальный ответ
                            if result["answer"]:
                                st.markdown("---")
                                st.subheader("💡 Полный ответ агента:")
                                st.markdown(result["answer"])
                                st.markdown("---")
                                
                                st.download_button(
                                    label="💾 Скачать ответ агента",
                                    data=result["answer"],
                                    file_name="agent_response.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                                
                        except Exception as e:
                            st.error(f"❌ Ошибка при работе агента: {str(e)}")
                            st.info("Попробуйте переформулировать вопрос.")
                else:
                    st.warning("⚠️ Пожалуйста, введите вопрос.")
        else:
            st.warning("⚠️ Агент не инициализирован. Пожалуйста, загрузите PDF файл и дождитесь его обработки.")

def render_info_section():
    """Рендерит информационную секцию когда файл не загружен"""
    st.info("👆 Загрузите PDF-файл для начала работы")
    
    with st.expander("ℹ️ Как это работает", expanded=True):
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
