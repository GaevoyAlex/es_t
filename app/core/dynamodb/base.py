
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.core.config import settings

class BaseDynamoDBConnector:

    
    def __init__(self):
        self.client = None
        self.dynamodb = None
        self._initialized = False
        self._tables = {}  # Кэш таблиц
    
    def _init_clients(self):

        try:


            self.client = boto3.client(
                'dynamodb',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            

            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
 
            self._test_connection()


        except Exception as e:
            print(f"[ERROR][DynamoDB] - Ошибка инициализации клиентов: {e}")
            raise e
    
    def _test_connection(self):

        try:

            list(self.dynamodb.tables.all())

        except Exception as e:
            print(f"[ERROR][DynamoDB] - Тест подключения: ОШИБКА - {e}")
            raise e
    
    def get_table(self, table_name: str):

        if table_name not in self._tables:
            self._tables[table_name] = self.dynamodb.Table(table_name)
        return self._tables[table_name]
    
    def table_exists(self, table_name: str) -> bool:

        try:
            self.client.describe_table(TableName=table_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise e
    
    def create_table_from_schema(self, table_schema) -> bool:

        table_name = table_schema.table_name
        
        try:
            if self.table_exists(table_name):
                print(f"[INFO][DynamoDB] - Таблица {table_name} уже существует")
                return True
            
            

            create_params = {
                'TableName': table_name,
                'KeySchema': table_schema.key_schema,
                'AttributeDefinitions': table_schema.attribute_definitions,
                'ProvisionedThroughput': table_schema.provisioned_throughput
            }
            

            if hasattr(table_schema, 'global_secondary_indexes'):
                create_params['GlobalSecondaryIndexes'] = table_schema.global_secondary_indexes
            

            self.client.create_table(**create_params)
            

            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"[INFO][DynamoDB] - Таблица {table_name} создана успешно")
            return True
            
        except Exception as e:
            print(f"[ERROR][DynamoDB] - Ошибка создания таблицы {table_name}: {e}")
            return False
    
    
    def create_item(self, table_name: str, item: Dict[str, Any]) -> Dict[str, Any]:

        try:

            if 'created_at' not in item:
                item['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in item:
                item['updated_at'] = datetime.utcnow().isoformat()
            
            table = self.get_table(table_name)
            table.put_item(Item=item)
            

            return item
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка создания элемента в {table_name}: {e}")
            raise e
    
    def get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        try:
            table = self.get_table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка получения элемента из {table_name}: {e}")
            return None
    
    def update_item(self, table_name: str, key: Dict[str, Any], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        try:

            updates['updated_at'] = datetime.utcnow().isoformat()
            

            update_expression = "SET "
            expression_values = {}
            
            for field, value in updates.items():
                update_expression += f"{field} = :{field}, "
                expression_values[f":{field}"] = value
            
            update_expression = update_expression.rstrip(", ")
            
            table = self.get_table(table_name)
            response = table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            return response.get('Attributes')
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка обновления элемента в {table_name}: {e}")
            return None
    
    def delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:

        try:
            table = self.get_table(table_name)
            table.delete_item(Key=key)

            return True
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка удаления элемента из {table_name}: {e}")
            return False
    
    def query_items(self, table_name: str, key_condition: Any, 
                   index_name: str = None, filter_expression: Any = None, 
                   limit: int = None) -> List[Dict[str, Any]]:

        try:
            table = self.get_table(table_name)
            
            query_params = {
                'KeyConditionExpression': key_condition
            }
            
            if index_name:
                query_params['IndexName'] = index_name
            if filter_expression:
                query_params['FilterExpression'] = filter_expression
            if limit:
                query_params['Limit'] = limit
            
            response = table.query(**query_params)
            return response.get('Items', [])
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка запроса к {table_name}: {e}")
            return []
    
    def scan_items(self, table_name: str, filter_expression: Any = None, 
                  limit: int = None) -> List[Dict[str, Any]]:

        try:
            table = self.get_table(table_name)
            
            scan_params = {}
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
            if limit:
                scan_params['Limit'] = limit
            
            response = table.scan(**scan_params)
            return response.get('Items', [])
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка сканирования {table_name}: {e}")
            return []
    
    def batch_write_items(self, table_name: str, items: List[Dict[str, Any]]) -> bool:

        try:
            table = self.get_table(table_name)
            

            batch_size = 25
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                with table.batch_writer() as batch_writer:
                    for item in batch:

                        if 'created_at' not in item:
                            item['created_at'] = datetime.utcnow().isoformat()
                        if 'updated_at' not in item:
                            item['updated_at'] = datetime.utcnow().isoformat()
                        
                        batch_writer.put_item(Item=item)
            
            return True
            
        except ClientError as e:
            print(f"[ERROR][DynamoDB] - Ошибка массовой записи в {table_name}: {e}")
            return False