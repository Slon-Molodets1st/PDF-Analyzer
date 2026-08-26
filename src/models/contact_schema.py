"""Модель для структурированного извлечения информации из контракта"""

from pydantic import BaseModel, Field
from typing import List, Optional

class ContractSchema(BaseModel):
    """Схема контракта для извлечения ключевой информации"""
    
    company_name: str = Field(
        description="Название компании-заказчика или исполнителя"
    )
    
    total_amount: int = Field(
        description="Сумма контракта в рублях (только цифры)"
    )
    
    signing_date: str = Field(
        description="Дата подписания контракта в формате ДД.ММ.ГГГГ"
    )
    
    risks: List[str] = Field(
        description="Список ключевых юридических и финансовых рисков, минимум 3 пункта",
        min_length=3
    )
    
    additional_terms: Optional[List[str]] = Field(
        default=None,
        description="Дополнительные важные условия контракта (опционально)"
    )
    
    class Config:
        """Конфигурация модели Pydantic"""
        json_schema_extra = {
            "example": {
                "company_name": "ООО 'ТехноСервис'",
                "total_amount": 5200000,
                "signing_date": "15.03.2024",
                "risks": [
                    "Несвоевременная поставка оборудования приведет к штрафным санкциям",
                    "Недостаточное качество оборудования может стать причиной судебных разбирательств",
                    "Отсутствие гарантийного обслуживания увеличивает эксплуатационные расходы"
                ],
                "additional_terms": ["Договор поставки оборудования"]
            }
        }
