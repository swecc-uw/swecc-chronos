import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer

class DynamoDBService:
    def __init__(self):
        self.client = boto3.resource('dynamodb')

    def create_health_metric_table(self):
        table_name = "health_metrics"

    
        tables = self.client.tables.all()
        table_names = [table.name for table in tables]
        if table_name in table_names:
            print(f"Table '{table_name}' already exists.")
            return

        else:
            try:
                table = self.client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'container_name',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'container_name',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
                print(f"Table '{table.table_name}' created successfully.")
     
            except ClientError as e:
                print(f"Error creating table: {e}")

    def delete_health_metric_table(self):
        table_name = "health_metrics"

        try:
            self.client.delete_table(TableName=table_name)
            print(f"Table '{table_name}' deleted successfully.")
        except ClientError as e:
            print(f"Failed to delete table '{table_name}': {e}")

    def add_item_to_table(self, table_name, item: dict):
        # item should be a dictionary
            table = self.client.Table(table_name)
            try:
                table.put_item(Item=item)
                print(f"Added item to table '{table_name}'")
            except ClientError as e:
                print(f"Failed to add item to table '{table_name}': {e}")

    def get_items_from_table(self, table_name):
        table = self.client.Table(table_name)
        try:
            response = table.scan()
            items = response['Items']
            return items
        except ClientError as e:
            print(f"Failed to get items from table '{table_name}': {e}")
            return []

db = DynamoDBService()