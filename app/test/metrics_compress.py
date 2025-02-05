import json
from app.models.container import DynamoHealthMetric
from app.services.dynamodb_service import db

def save_mock_data(table_name: str, output_file: str = "mockdata.py"):
    """Fetch data from DynamoDB and save it as a Python list in mockdata.py"""
    raw_items = db.get_items_from_table(table_name)

    # Convert DynamoDB items to `DynamoHealthMetric` objects
    parsed_items = [DynamoHealthMetric(**item).model_dump() for item in raw_items]

    # Save to a Python file as a list
    with open(output_file, "w") as f:
        f.write(f"mockdata = {json.dumps(parsed_items, indent=4)}\n")