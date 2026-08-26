"""Модель для результатов поиска противоречий"""

from pydantic import BaseModel, Field
from typing import Literal

class ContradictionResult(BaseModel):
    """Результат поиска противоречия в документе"""
    
    block_number: int = Field(
        description="Номер блока, где найдено противоречие"
    )
    
    contradiction_type: Literal[
        "финансовое", 
        "юридическое", 
        "логическое", 
        "терминологическое"
    ] = Field(
        description="Тип противоречия: финансовое, юридическое, логическое, терминологическое"
    )
    
    previous_statement: str = Field(
        description="Утверждение из предыдущего блока"
    )
    
    current_statement: str = Field(
        description="Противоречащее утверждение из текущего блока"
    )
    
    explanation: str = Field(
        description="Объяснение противоречия"
    )
    
    severity: Literal[
        "критическое",
        "высокое", 
        "среднее", 
        "низкое"
    ] = Field(
        description="Степень серьезности: критическое, высокое, среднее, низкое"
    )
    
    class Config:
        """Конфигурация модели Pydantic"""
        json_schema_extra = {
            "example": {
                "block_number": 3,
                "contradiction_type": "финансовое",
                "previous_statement": "Сумма контракта составляет 5 000 000 рублей",
                "current_statement": "Общая стоимость работ равна 7 500 000 рублей",
                "explanation": "В блоке 1 указана сумма 5 млн, а в блоке 3 - 7.5 млн",
                "severity": "высокое"
            }
        }
