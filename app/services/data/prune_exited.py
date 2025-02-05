from datetime import datetime, timedelta
from typing import List
from app.models.container import DynamoHealthMetric
from app.services.data.data_compact import DataCompactStrategy


class PruneExitedAfterDays(DataCompactStrategy):
    def __init__(self, time_threshold: int = 14):
        self.time_threshold = time_threshold

    def compact(self, data: List[DynamoHealthMetric]) -> List[DynamoHealthMetric]:
        data = self.check_data(data)

        two_weeks_ago = datetime.now() - timedelta(days=self.time_threshold)
        
        filtered_data = [item for item in data if datetime.fromisoformat(item.timestamp) < two_weeks_ago]

        prune_data = [item for item in filtered_data if item.status == "exited" and item.started_at is None and item.finished_at is None]

        result_data = [item for item in data if item not in prune_data]
        return result_data
    
    def __str__(self):
        return f"PruneExitedAfterDays({self.time_threshold})"