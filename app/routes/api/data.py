from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.security import get_current_user
from app.core.dynamodb.connector import get_generic_repository, get_db_connector

router = APIRouter()


@router.post("/tables/{table_name}/items")
async def create_item(
    table_name: str,
    item_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):

    try:
        repo = get_generic_repository(table_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="База данных недоступна"
            )
        
        item_data['created_by'] = current_user['id']
        item_data['created_by_email'] = current_user['email']
        
        created_item = repo.create(item_data)
        
        
        return {
            "message": "Элемент успешно создан",
            "table_name": table_name,
            "item_id": created_item['id'],
            "created_by": current_user['email'],
            "item": created_item
        }
        
    except Exception as e:
        print(f"[ERROR][API] - Ошибка создания элемента в {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания элемента: {str(e)}"
        )

@router.get("/tables/{table_name}/items/{item_id}")
async def get_item(
    table_name: str,
    item_id: str,
    current_user = Depends(get_current_user)
):
    try:
        repo = get_generic_repository(table_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="База данных недоступна"
            )
        
        item = repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Элемент не найден"
            )
        
        return {
            "table_name": table_name,
            "item_id": item_id,
            "item": item,
            "requested_by": current_user['email']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][API] - Ошибка получения элемента {item_id} из {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения элемента: {str(e)}"
        )

@router.put("/tables/{table_name}/items/{item_id}")
async def update_item(
    table_name: str,
    item_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    try:
        repo = get_generic_repository(table_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="База данных недоступна"
            )
        
        existing_item = repo.get_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Элемент не найден"
            )
        
        updates['updated_by'] = current_user['id']
        updates['updated_by_email'] = current_user['email']
        
        updated_item = repo.update_by_id(item_id, updates)
        
        print(f"[INFO][API] - Элемент {item_id} обновлен в таблице {table_name} пользователем {current_user['email']}")
        
        return {
            "message": "Элемент успешно обновлен",
            "table_name": table_name,
            "item_id": item_id,
            "updated_by": current_user['email'],
            "item": updated_item
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][API] - Ошибка обновления элемента {item_id} в {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления элемента: {str(e)}"
        )

@router.delete("/tables/{table_name}/items/{item_id}")
async def delete_item(
    table_name: str,
    item_id: str,
    current_user = Depends(get_current_user)
):
    try:
        repo = get_generic_repository(table_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="База данных недоступна"
            )
        
        existing_item = repo.get_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Элемент не найден"
            )
        
        success = repo.delete_by_id(item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления элемента"
            )
        
        print(f"[INFO][API] - Элемент {item_id} удален из таблицы {table_name} пользователем {current_user['email']}")
        
        return {
            "message": "Элемент успешно удален",
            "table_name": table_name,
            "item_id": item_id,
            "deleted_by": current_user['email']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][API] - Ошибка удаления элемента {item_id} из {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления элемента: {str(e)}"
        )

# =============== СПИСКИ И ПОИСК ================

@router.get("/tables/{table_name}/items")
async def list_items(
    table_name: str,
    limit: Optional[int] = Query(default=50, le=1000),
    current_user = Depends(get_current_user)
):
    try:
        repo = get_generic_repository(table_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="База данных недоступна"
            )
        
        items = repo.list_all(limit=limit)
        
        return {
            "table_name": table_name,
            "total_items": len(items),
            "limit": limit,
            "items": items,
            "requested_by": current_user['email']
        }
        
    except Exception as e:
        print(f"[ERROR][API] - Ошибка получения списка из {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения списка: {str(e)}"
        )

@router.get("/tables/{table_name}/search")
async def search_items(
    table_name: str,
    field: str = Query(..., description="Поле для поиска"),
    value: str = Query(..., description="Значение для поиска"),
    search_type: str = Query(default="exact", regex="^(exact|contains)$"),
    current_user = Depends(get_current_user)
):
   
    # Поиск элементов по полю
    # search_type: exact (точное совпадение) или contains (содержит)

    try:
        repo = get_generic_repository(table_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="База данных недоступна"
            )
        
        if search_type == "exact":
            items = repo.find_by_field(field, value)
        elif search_type == "contains":
            items = repo.search_by_pattern(field, value)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный тип поиска"
            )
        
        return {
            "table_name": table_name,
            "search_field": field,
            "search_value": value,
            "search_type": search_type,
            "results_count": len(items),
            "items": items,
            "searched_by": current_user['email']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][API] - Ошибка поиска в {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка поиска: {str(e)}"
        )

