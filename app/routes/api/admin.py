from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from app.core.permissions import require_admin
from app.core.dynamodb.connector import get_generic_repository, get_db_connector
from app.core.security import get_admin_user
from app.models.market import Token, TokenStats, Exchange, ExchangesStats
from app.crud.user import update_user_role

router = APIRouter()

@router.post("/tokens")
async def create_token(token_data: Dict[str, Any], current_user = Depends(require_admin)):
    try:
        repo = get_generic_repository("LiberandumAggregationToken")
        
        token_data.update({
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_deleted': False,
            'created_by_admin': current_user['id']
        })
        
        created_token = repo.create(token_data, auto_id=False)
        
        return {
            "message": "Токен создан",
            "token": created_token,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания токена: {str(e)}")

@router.get("/tokens")
async def list_tokens(limit: Optional[int] = Query(default=500), current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationToken")
        items = repo.scan_items("LiberandumAggregationToken", limit=limit)
        active_tokens = [token for token in items if not token.get('is_deleted', False)]
        
        return {
            "total": len(active_tokens),
            "tokens": active_tokens,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения токенов: {str(e)}")

@router.get("/tokens/{token_id}")
async def get_token(token_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationToken")
        token = repo.get_by_id(token_id)
        
        if not token:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
        
        return {
            "token": token,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения токена: {str(e)}")

@router.put("/tokens/{token_id}")
async def update_token(token_id: str, updates: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationToken")
        
        existing_token = repo.get_by_id(token_id)
        if not existing_token:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
        
        updates.update({
            'updated_at': datetime.now().isoformat(),
            'updated_by_admin': current_user['id']
        })
        
        updated_token = repo.update_by_id(token_id, updates)
        
        return {
            "message": "Токен обновлен",
            "token": updated_token,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка обновления токена: {str(e)}")

@router.delete("/tokens/{token_id}")
async def delete_token(token_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationToken")
        
        existing_token = repo.get_by_id(token_id)
        if not existing_token:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
        
        repo.update_by_id(token_id, {
            'is_deleted': True,
            'deleted_at': datetime.now().isoformat(),
            'deleted_by_admin': current_user['id']
        })
        
        return {
            "message": "Токен удален",
            "token_id": token_id,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка удаления токена: {str(e)}")

@router.post("/token-stats")
async def create_token_stats(stats_data: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationTokenStats")
        
        stats_data.update({
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_deleted': False,
            'created_by_admin': current_user['id']
        })
        
        created_stats = repo.create(stats_data, auto_id=False)
        
        return {
            "message": "Статистика токена создана",
            "stats": created_stats,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания статистики: {str(e)}")

@router.get("/token-stats")
async def list_token_stats(limit: Optional[int] = Query(default=500), current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationTokenStats")
        items = repo.scan_items("LiberandumAggregationTokenStats", limit=limit)
        active_stats = [stats for stats in items if not stats.get('is_deleted', False)]
        
        return {
            "total": len(active_stats),
            "token_stats": active_stats,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/token-stats/{stats_id}")
async def get_token_stats(stats_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationTokenStats")
        stats = repo.get_by_id(stats_id)
        
        if not stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статистика не найдена")
        
        return {
            "stats": stats,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения статистики: {str(e)}")

@router.put("/token-stats/{stats_id}")
async def update_token_stats(stats_id: str, updates: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationTokenStats")
        
        existing_stats = repo.get_by_id(stats_id)
        if not existing_stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статистика не найдена")
        
        updates.update({
            'updated_at': datetime.now().isoformat(),
            'updated_by_admin': current_user['id']
        })
        
        updated_stats = repo.update_by_id(stats_id, updates)
        
        return {
            "message": "Статистика обновлена",
            "stats": updated_stats,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка обновления статистики: {str(e)}")

@router.delete("/token-stats/{stats_id}")
async def delete_token_stats(stats_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationTokenStats")
        
        existing_stats = repo.get_by_id(stats_id)
        if not existing_stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статистика не найдена")
        
        repo.update_by_id(stats_id, {
            'is_deleted': True,
            'deleted_at': datetime.now().isoformat(),
            'deleted_by_admin': current_user['id']
        })
        
        return {
            "message": "Статистика удалена",
            "stats_id": stats_id,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка удаления статистики: {str(e)}")

@router.post("/exchanges")
async def create_exchange(exchange_data: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchanges")
        
        exchange_data.update({
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_deleted': False,
            'created_by_admin': current_user['id']
        })
        
        created_exchange = repo.create(exchange_data, auto_id=False)
        
        return {
            "message": "Биржа создана",
            "exchange": created_exchange,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания биржи: {str(e)}")

@router.get("/exchanges")
async def list_exchanges(limit: Optional[int] = Query(default=250), current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchanges")
        items = repo.scan_items("LiberandumAggregationExchanges", limit=limit)
        active_exchanges = [exchange for exchange in items if not exchange.get('is_deleted', False)]
        
        return {
            "total": len(active_exchanges),
            "exchanges": active_exchanges,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения бирж: {str(e)}")

@router.get("/exchanges/{exchange_id}")
async def get_exchange(exchange_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchanges")
        exchange = repo.get_by_id(exchange_id)
        
        if not exchange:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Биржа не найдена")
        
        return {
            "exchange": exchange,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения биржи: {str(e)}")

@router.put("/exchanges/{exchange_id}")
async def update_exchange(exchange_id: str, updates: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchanges")
        
        existing_exchange = repo.get_by_id(exchange_id)
        if not existing_exchange:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Биржа не найдена")
        
        updates.update({
            'updated_at': datetime.now().isoformat(),
            'updated_by_admin': current_user['id']
        })
        
        updated_exchange = repo.update_by_id(exchange_id, updates)
        
        return {
            "message": "Биржа обновлена",
            "exchange": updated_exchange,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка обновления биржи: {str(e)}")

@router.delete("/exchanges/{exchange_id}")
async def delete_exchange(exchange_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchanges")
        
        existing_exchange = repo.get_by_id(exchange_id)
        if not existing_exchange:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Биржа не найдена")
        
        repo.update_by_id(exchange_id, {
            'is_deleted': True,
            'deleted_at': datetime.now().isoformat(),
            'deleted_by_admin': current_user['id']
        })
        
        return {
            "message": "Биржа удалена",
            "exchange_id": exchange_id,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка удаления биржи: {str(e)}")

@router.post("/exchange-stats")
async def create_exchange_stats(stats_data: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchangesStats")
        
        stats_data.update({
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_deleted': False,
            'created_by_admin': current_user['id']
        })
        
        created_stats = repo.create(stats_data, auto_id=False)
        
        return {
            "message": "Статистика биржи создана",
            "stats": created_stats,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания статистики: {str(e)}")

@router.get("/exchange-stats")
async def list_exchange_stats(limit: Optional[int] = Query(default=50), current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchangesStats")
        items = repo.scan_items("LiberandumAggregationExchangesStats", limit=limit)
        active_stats = [stats for stats in items if not stats.get('is_deleted', False)]
        
        return {
            "total": len(active_stats),
            "exchange_stats": active_stats,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/exchange-stats/{stats_id}")
async def get_exchange_stats(stats_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchangesStats")
        stats = repo.get_by_id(stats_id)
        
        if not stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статистика не найдена")
        
        return {
            "stats": stats,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения статистики: {str(e)}")

@router.put("/exchange-stats/{stats_id}")
async def update_exchange_stats(stats_id: str, updates: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchangesStats")
        
        existing_stats = repo.get_by_id(stats_id)
        if not existing_stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статистика не найдена")
        
        updates.update({
            'updated_at': datetime.now().isoformat(),
            'updated_by_admin': current_user['id']
        })
        
        updated_stats = repo.update_by_id(stats_id, updates)
        
        return {
            "message": "Статистика обновлена",
            "stats": updated_stats,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка обновления статистики: {str(e)}")

@router.delete("/exchange-stats/{stats_id}")
async def delete_exchange_stats(stats_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("LiberandumAggregationExchangesStats")
        
        existing_stats = repo.get_by_id(stats_id)
        if not existing_stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статистика не найдена")
        
        repo.update_by_id(stats_id, {
            'is_deleted': True,
            'deleted_at': datetime.now().isoformat(),
            'deleted_by_admin': current_user['id']
        })
        
        return {
            "message": "Статистика удалена",
            "stats_id": stats_id,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка удаления статистики: {str(e)}")

@router.get("/users")
async def list_users(limit: Optional[int] = Query(default=50), current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("users")
        items = repo.scan_items("users", limit=limit)
        active_users = [user for user in items if user.get('is_active', True)]
        
        for user in active_users:
            user.pop('hashed_password', None)
            user.pop('access_token', None)
            user.pop('refresh_token', None)
        
        return {
            "total": len(active_users),
            "users": active_users,
            "admin": current_user['email']
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения пользователей: {str(e)}")

@router.get("/users/{user_id}")
async def get_user_by_admin(user_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("users")
        user = repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        
        user.pop('hashed_password', None)
        user.pop('access_token', None)
        user.pop('refresh_token', None)
        
        return {
            "user": user,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения пользователя: {str(e)}")

@router.put("/users/{user_id}")
async def update_user_by_admin(user_id: str, updates: Dict[str, Any], current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("users")
        
        existing_user = repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        
        if 'hashed_password' in updates or 'password' in updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Изменение пароля запрещено через этот эндпоинт")
        
        updates.update({
            'updated_at': datetime.now().isoformat(),
            'updated_by_admin': current_user['id']
        })
        
        updated_user = repo.update_by_id(user_id, updates)
        updated_user.pop('hashed_password', None)
        updated_user.pop('access_token', None)
        updated_user.pop('refresh_token', None)
        
        return {
            "message": "Пользователь обновлен администратором",
            "user": updated_user,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка обновления пользователя: {str(e)}")

@router.put("/users/{user_id}/role")
async def update_user_role_by_admin(user_id: str, role: str, current_user = Depends(get_admin_user)):
    try:
        valid_roles = ['user', 'pro_user', 'admin']
        if role not in valid_roles:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недопустимая роль. Доступные: {', '.join(valid_roles)}")
        
        updated_user = update_user_role(user_id, role)
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        
        return {
            "message": f"Роль пользователя изменена на {role}",
            "user_id": user_id,
            "new_role": role,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка изменения роли: {str(e)}")

@router.put("/users/{user_id}/deactivate")
async def deactivate_user_by_admin(user_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("users")
        
        existing_user = repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        
        if user_id == current_user['id']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя деактивировать самого себя")
        
        updated_user = repo.update_by_id(user_id, {
            'is_active': False,
            'deactivated_at': datetime.now().isoformat(),
            'deactivated_by_admin': current_user['id']
        })
        
        return {
            "message": "Пользователь деактивирован",
            "user_id": user_id,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка деактивации пользователя: {str(e)}")

@router.put("/users/{user_id}/activate")
async def activate_user_by_admin(user_id: str, current_user = Depends(get_admin_user)):
    try:
        repo = get_generic_repository("users")
        
        existing_user = repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        
        updated_user = repo.update_by_id(user_id, {
            'is_active': True,
            'activated_at': datetime.now().isoformat(),
            'activated_by_admin': current_user['id']
        })
        
        return {
            "message": "Пользователь активирован",
            "user_id": user_id,
            "admin": current_user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка активации пользователя: {str(e)}")