from abc import ABC, abstractmethod
from typing import List

from app.models.container import DynamoHealthMetric


class DataCompactStrategy(ABC):
    @abstractmethod
    def compact(self, data: List[DynamoHealthMetric]) -> List[DynamoHealthMetric]:
        pass

    def __str__(self):
        return self.__class__.__name__
    
    def check_data(self, data: List[DynamoHealthMetric]) -> List[DynamoHealthMetric]:
        if not data:
            return []
        if isinstance(data, list) and isinstance(data[0], dict):
            return [DynamoHealthMetric(**item) for item in data]
        return data

class DataCompactManager:
    def __init__(self, compacter_list: List[DataCompactStrategy]):
        self.compacter_list = compacter_list

    def compact(self, data: List[DynamoHealthMetric]) -> List[DynamoHealthMetric]:
        for compacter in self.compacter_list:
            data = compacter.compact(data)
        return data

    def clear_pipeline(self):
        self.compacter_list.clear()

    def add_compacter(self, compacter: DataCompactStrategy):
        self.compacter_list.append(compacter)

    def remove_compacter(self, compacter: DataCompactStrategy):
        self.compacter_list.remove(compacter)

    def set_pipeline(self, compacter_list: List[DataCompactStrategy]):
        self.compacter_list = compacter_list

    def get_current_pipeline(self) -> List[str]:
        return [str(compacter) for compacter in self.compacter_list]
    
