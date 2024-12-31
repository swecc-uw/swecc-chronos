import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

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
        
    def get_recent_items_from_table(self, table_name):
        table = self.client.Table(table_name)
        one_week_ago = datetime.now() - timedelta(weeks=1)
        one_week_ago_str = one_week_ago.strftime('%Y-%m-%dT%H:%M:%S')

        try:
            response = table.scan(
            FilterExpression='#ts >= :one_week_ago',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':one_week_ago': one_week_ago_str}
            )
            items = response['Items']
            return items
        except ClientError as e:
            print(f"Failed to get recent items from table '{table_name}': {e}")
            return []
        
    def get_time_range_items_from_table(self, table_name, start_time, end_time):
        table = self.client.Table(table_name)
        try:
            response = table.scan(
            FilterExpression='#ts BETWEEN :start_time AND :end_time',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':start_time': start_time, ':end_time': end_time}
            )
            items = response['Items']
            return items
        except ClientError as e:
            print(f"Failed to get items from table '{table_name}': {e}")
            return []
        
    def get_recent_items_by_container_name(self, table_name, container_name):
        table = self.client.Table(table_name)
        one_week_ago = datetime.now() - timedelta(weeks=1)
        one_week_ago_str = one_week_ago.strftime('%Y-%m-%dT%H:%M:%S')

        try:
            response = table.scan(
            FilterExpression='#cn = :container_name AND #ts >= :one_week_ago',
            ExpressionAttributeNames={'#ts': 'timestamp', '#cn': 'container_name'},
            ExpressionAttributeValues={':container_name': container_name, ':one_week_ago': one_week_ago_str}
            )
            items = response['Items']
            return items
        except ClientError as e:
            print(f"Failed to get recent items from table '{table_name}': {e}")
            return []
        
    def get_all_items_by_container_name(self, table_name, container_name):
        table = self.client.Table(table_name)
        try:
            response = table.scan(
            FilterExpression='#cn = :container_name',
            ExpressionAttributeNames={'#cn': 'container_name'},
            ExpressionAttributeValues={':container_name': container_name}
            )
            items = response['Items']
            return items
        except ClientError as e:
            print(f"Failed to get items from table '{table_name}': {e}")
            return []

db = DynamoDBService()