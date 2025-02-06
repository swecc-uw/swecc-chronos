from datetime import datetime, timedelta
import json
from typing import List
from app.models.container import DynamoHealthMetric
from app.services.dynamodb_service import db
from app.services.data.data_compact import DataCompactManager
from app.services.data.prune_exited import PruneExitedAfterDays
from app.services.data.reduce_by_ten import ReduceByTenForEachContainer
from app.test.mock_data.metrics import METRICS_MOCK_DATA
from app.utils.task import compact_data_task

def write_to_file(data: List[DynamoHealthMetric], output_file: str = "compacted.py", variable_name: str = "compacted_data"):
    """Write the data to a Python file"""
    data = [item.model_dump() for item in data]

    with open(output_file, "w") as f:
        f.write(f"{variable_name} = {json.dumps(data, indent=4)}\n")

def save_mock_data(table_name: str, output_file: str = "mockdata.py"):
    """Fetch data from DynamoDB and save it as a Python list in mockdata.py"""
    raw_items = db.get_items_from_table(table_name)

    # Convert DynamoDB items to `DynamoHealthMetric` objects
    parsed_items = [DynamoHealthMetric(**item) for item in raw_items]

    write_to_file(parsed_items, output_file, "METRICS_MOCK_DATA")
    # Save to a Python file as a list
    with open(output_file, "w") as f:
        f.write(f"mockdata = {json.dumps(parsed_items, indent=4)}\n")

two_weeks_ago = datetime.now() - timedelta(days=14)
data: List[DynamoHealthMetric] = METRICS_MOCK_DATA
filtered_data: List[DynamoHealthMetric] = [item for item in data if datetime.fromisoformat(item["timestamp"]) < two_weeks_ago]

compact_manager = DataCompactManager([PruneExitedAfterDays(), ReduceByTenForEachContainer()])
compacted = compact_manager.compact(filtered_data)
print(compact_manager.get_current_pipeline())
print(f"Original data length: {len(filtered_data)}")
print(f"Compacted data length: {len(compacted)}")
print(f"Data compacted by: {len(filtered_data) - len(compacted)}")
write_to_file(compacted)