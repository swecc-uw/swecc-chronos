from abc import ABC, abstractmethod
from typing import List

from app.models.container import DynamoHealthMetric


class DataCompactStrategy(ABC):
    @abstractmethod
    def compact(self, data: List[DynamoHealthMetric]) -> List[DynamoHealthMetric]:
        pass

    def __str__(self):
        return self.__class__.__name__

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
    
