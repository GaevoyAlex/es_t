from typing import Dict, Any, Optional

from app.core.dynamodb.repositories.otp import OTPRepository
from .base import BaseDynamoDBConnector
from .repositories.user import UserRepository
from .repositories.generic import GenericRepository

class DynamoDBConnector(BaseDynamoDBConnector):
    
    def __init__(self):
        super().__init__()
        
        self.users: Optional[UserRepository] = None
        self.otp: Optional[OTPRepository] = None
        
        self._generic_repositories: Dict[str, GenericRepository] = {}
    
    def initiate_connection(self) -> 'DynamoDBConnector':

        if self._initialized:
            return self
        
        self._init_clients()
                
        self._init_repositories()
        
        self._initialized = True
        return self
    
    def _create_default_tables(self):

        try:

            from app.aws.table_schemas import (
                users_schema, otp_schema,
                tokens_schema, token_stats_schema,
                exchanges_schema, exchange_stats_schema
            )
            
            schemas = [
                (users_schema, 'users'),
                (otp_schema, 'otp_codes'),
                (tokens_schema, 'tokens'),
                (token_stats_schema, 'token_stats'),
                (exchanges_schema, 'exchanges'),
                (exchange_stats_schema, 'exchange_stats')
            ]
            
            for schema, description in schemas:
                try:
                    self.create_table_from_schema(schema)
                    print(f"[INFO][DynamoDB] - Таблица {description} проверена/создана")
                except Exception as e:
                    print(f"[ERROR][DynamoDB] - Ошибка создания таблицы {description}: {e}")
                    
        except ImportError as e:
            print(f"[ERROR][DynamoDB] - Ошибка импорта схем: {e}")
    
    def _init_repositories(self):

        from app.core.config import settings
        
        try:

            self.users = UserRepository(settings.DYNAMODB_USERS_TABLE)
            self.users._init_clients()
            self.users._initialized = True
            
            self.otp = OTPRepository(settings.DYNAMODB_OTP_TABLE)
            self.otp._init_clients()
            self.otp._initialized = True
            
            print("[INFO][DynamoDB] - Репозитории инициализированы")
            
        except Exception as e:
            print(f"[ERROR][DynamoDB] - Ошибка инициализации репозиториев: {e}")
    
    # =============== УНИВЕРСАЛЬНЫЕ РЕПОЗИТОРИИ ===============
    
    def get_repository(self, table_name: str) -> GenericRepository:

        if table_name not in self._generic_repositories:
            repo = GenericRepository(table_name)
            repo._init_clients()
            repo._initialized = True
            self._generic_repositories[table_name] = repo
            print(f"[INFO][DynamoDB] - Создан универсальный репозиторий для таблицы: {table_name}")
        
        return self._generic_repositories[table_name]
    
    def create_custom_table(self, table_name: str, 
                          key_schema: list, 
                          attribute_definitions: list,
                          provisioned_throughput: dict = None,
                          global_secondary_indexes: list = None) -> bool:
       
        try:
            if self.table_exists(table_name):
                print(f"[INFO][DynamoDB] - Таблица {table_name} уже существует")
                return True
            
            if not provisioned_throughput:
                provisioned_throughput = {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            
            create_params = {
                'TableName': table_name,
                'KeySchema': key_schema,
                'AttributeDefinitions': attribute_definitions,
                'ProvisionedThroughput': provisioned_throughput
            }
            
            if global_secondary_indexes:
                create_params['GlobalSecondaryIndexes'] = global_secondary_indexes
            
            self.client.create_table(**create_params)
            
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            return True
            
        except Exception as e:
            print(f"[ERROR][DynamoDB] - Ошибка создания кастомной таблицы {table_name}: {e}")
            return False
    
    
    def get_system_info(self) -> Dict[str, Any]:

        try:

            all_tables = list(self.dynamodb.tables.all())
            table_names = [table.name for table in all_tables]
            
            repo_info = {
                'users': bool(self.users),
                'otp': bool(self.otp),
                'generic_repositories': list(self._generic_repositories.keys())
            }
            
            return {
                'status': 'connected',
                'initialized': self._initialized,
                'region': self.client._client_config.__dict__.get('region_name'),
                'total_tables': len(table_names),
                'table_names': table_names,
                'repositories': repo_info,
                'cached_tables': len(self._tables)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'initialized': self._initialized
            }
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:

        try:
            table_description = self.client.describe_table(TableName=table_name)
            table_info = table_description['Table']
            
            repo = self.get_repository(table_name)
            stats = repo.get_stats()
            
            return {
                'table_name': table_name,
                'table_status': table_info.get('TableStatus'),
                'creation_date': str(table_info.get('CreationDateTime')),
                'item_count': table_info.get('ItemCount'),
                'table_size_bytes': table_info.get('TableSizeBytes'),
                'key_schema': table_info.get('KeySchema'),
                'global_secondary_indexes': table_info.get('GlobalSecondaryIndexes', []),
                'data_stats': stats
            }
            
        except Exception as e:
            return {
                'table_name': table_name,
                'status': 'error',
                'error': str(e)
            }
    
    
    def cleanup_all_expired_data(self) -> Dict[str, int]:

        results = {}
        
        if self.otp:
            results['otp_codes'] = self.otp.cleanup_expired_otps()

        return results
    
    def backup_table_data(self, table_name: str) -> Dict[str, Any]:

        try:
            repo = self.get_repository(table_name)
            backup_data = repo.export_to_dict()
            
            return backup_data
            
        except Exception as e:
            print(f"[ERROR][DynamoDB] - Ошибка создания резервной копии {table_name}: {e}")
            return {'error': str(e)}

connector = DynamoDBConnector()

def get_db_connector() -> DynamoDBConnector:

    if not connector._initialized:
        try:
            connector.initiate_connection()
            print("[INFO][DynamoDB] - Коннектор инициализирован")
        except Exception as e:
            print(f"[ERROR][DynamoDB] - Критическая ошибка инициализации: {e}")
            return None
    return connector

def get_user_repository() -> UserRepository:
    conn = get_db_connector()
    return conn.users if conn else None

def get_otp_repository() -> OTPRepository:
    conn = get_db_connector()
    return conn.otp if conn else None

def get_generic_repository(table_name: str) -> GenericRepository:
    conn = get_db_connector()
    return conn.get_repository(table_name) if conn else None