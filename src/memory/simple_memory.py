"""Простая реализация памяти для цепей"""

from typing import Dict, Any, List

class SimpleMemory:
    """
    Простая реализация памяти без внешних зависимостей
    Используется для хранения истории анализа блоков
    """
    
    def __init__(self):
        """Инициализация памяти"""
        self.history: List[Dict] = []
        self.summary: str = "Нет предыдущих блоков."
    
    def save_context(self, input_data: Dict, output_data: str) -> None:
        """
        Сохраняет контекст в память
        
        Args:
            input_data: входные данные
            output_data: выходные данные
        """
        self.history.append({
            "input": input_data,
            "output": output_data
        })
        if len(self.history) > 0:
            self._update_summary()
    
    def _update_summary(self) -> None:
        """Обновляет краткое содержание истории"""
        if len(self.history) <= 2:
            summary_parts = []
            for i, item in enumerate(self.history, 1):
                summary_parts.append(f"Блок {i}: {item['output'][:200]}...")
            self.summary = "\n".join(summary_parts)
        else:
            last_items = self.history[-3:]
            summary_parts = []
            for i, item in enumerate(last_items, len(self.history) - 2):
                summary_parts.append(f"Блок {i}: {item['output'][:200]}...")
            self.summary = f"Всего проанализировано {len(self.history)} блоков. Последние результаты:\n" + "\n".join(summary_parts)
    
    def load_memory_variables(self) -> Dict[str, str]:
        """
        Загружает переменные памяти
        
        Returns:
            Dict[str, str]: словарь с переменными памяти
        """
        return {"memory_summary": self.summary}
    
    def clear(self) -> None:
        """Очищает память"""
        self.history = []
        self.summary = "Нет предыдущих блоков."
