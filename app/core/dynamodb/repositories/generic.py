from typing import Dict, Any, Optional, List, Union
from boto3.dynamodb.conditions import Key, Attr
import uuid
from datetime import datetime

from ..base import BaseDynamoDBConnector

class GenericRepository(BaseDynamoDBConnector):

    
    def __init__(self, table_name: str):
        super().__init__()
        self.table_name = table_name
    
    
    def create(self, data: Dict[str, Any], auto_id: bool = True) -> Dict[str, Any]:

        if auto_id and 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        return self.create_item(self.table_name, data)
    
    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:

        return self.get_item(self.table_name, {'id': item_id})
    
    def update_by_id(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        return self.update_item(
            self.table_name,
            key={'id': item_id},
            updates=updates
        )
    
    def delete_by_id(self, item_id: str) -> bool:

        return self.delete_item(self.table_name, {'id': item_id})
    
    def list_all(self, limit: int = None) -> List[Dict[str, Any]]:

        return self.scan_items(self.table_name, limit=limit)
    
 
    
    def find_by_field(self, field_name: str, field_value: Any, 
                     index_name: str = None) -> List[Dict[str, Any]]:

        if index_name:
            return self.query_items(
                self.table_name,
                key_condition=Key(field_name).eq(field_value),
                index_name=index_name
            )
        else:
            return self.scan_items(
                self.table_name,
                filter_expression=Attr(field_name).eq(field_value)
            )
    
    def find_by_multiple_fields(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:

        filter_expressions = []
        for field, value in filters.items():
            filter_expressions.append(Attr(field).eq(value))
        
        combined_filter = filter_expressions[0]
        for expr in filter_expressions[1:]:
            combined_filter = combined_filter & expr
        
        return self.scan_items(self.table_name, filter_expression=combined_filter)
    
    def search_by_pattern(self, field_name: str, pattern: str) -> List[Dict[str, Any]]:

        return self.scan_items(
            self.table_name,
            filter_expression=Attr(field_name).contains(pattern)
        )
    
    def find_in_date_range(self, date_field: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:

        return self.scan_items(
            self.table_name,
            filter_expression=Attr(date_field).between(start_date, end_date)
        )
    
    def find_recent(self, date_field: str = 'created_at', limit: int = 10) -> List[Dict[str, Any]]:


        items = self.scan_items(self.table_name)
        
        try:
            sorted_items = sorted(
                items, 
                key=lambda x: x.get(date_field, ''), 
                reverse=True
            )
            return sorted_items[:limit]
        except:
            return items[:limit]
    
    
    def count_total(self) -> int:

        response = self.get_table(self.table_name).scan(Select='COUNT')
        return response.get('Count', 0)
    
    def count_by_field(self, field_name: str, field_value: Any) -> int:

        items = self.find_by_field(field_name, field_value)
        return len(items)
    
    def get_field_values(self, field_name: str) -> List[Any]:

        items = self.scan_items(self.table_name)
        values = set()
        for item in items:
            if field_name in item:
                values.add(item[field_name])
        return list(values)
    
    def get_stats(self) -> Dict[str, Any]:

        items = self.scan_items(self.table_name)
        
        if not items:
            return {
                'total_items': 0,
                'table_name': self.table_name,
                'created_at': datetime.utcnow().isoformat()
            }
        
        field_counts = {}
        for item in items:
            for field in item.keys():
                field_counts[field] = field_counts.get(field, 0) + 1
        
        oldest_item = min(items, key=lambda x: x.get('created_at', ''), default={})
        newest_item = max(items, key=lambda x: x.get('created_at', ''), default={})
        
        return {
            'table_name': self.table_name,
            'total_items': len(items),
            'fields': list(field_counts.keys()),
            'field_coverage': field_counts,
            'oldest_record': oldest_item.get('created_at'),
            'newest_record': newest_item.get('created_at'),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    


    def bulk_create(self, items: List[Dict[str, Any]], auto_id: bool = True) -> bool:

        if auto_id:
            for item in items:
                if 'id' not in item:
                    item['id'] = str(uuid.uuid4())
        
        return self.batch_write_items(self.table_name, items)
    
    def bulk_delete_by_ids(self, item_ids: List[str]) -> int:

        deleted_count = 0
        for item_id in item_ids:
            if self.delete_by_id(item_id):
                deleted_count += 1
        return deleted_count
    
    def cleanup_old_records(self, date_field: str = 'created_at', 
                          days_old: int = 30) -> int:

        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
        
        old_items = self.scan_items(
            self.table_name,
            filter_expression=Attr(date_field).lt(cutoff_date)
        )
        
        deleted_count = 0
        for item in old_items:
            if self.delete_by_id(item['id']):
                deleted_count += 1
        
        return deleted_count
    
    
    def export_to_dict(self, limit: int = None) -> Dict[str, Any]:

        items = self.list_all(limit)
        
        return {
            'table_name': self.table_name,
            'export_timestamp': datetime.utcnow().isoformat(),
            'total_items': len(items),
            'items': items
        }
    
    def import_from_dict(self, data: Dict[str, Any], 
                        clear_existing: bool = False) -> bool:

        try:
            if clear_existing:
                existing_items = self.list_all()
                for item in existing_items:
                    self.delete_by_id(item['id'])
                print(f"[INFO] Удалено {len(existing_items)} существующих записей")
            
            items = data.get('items', [])
            if items:
                success = self.bulk_create(items, auto_id=False)
                if success:
                    print(f"[INFO] Импортировано {len(items)} записей в {self.table_name}")
                return success
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка импорта в {self.table_name}: {e}")
            return False