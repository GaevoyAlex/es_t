import json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, logger, status, Query, Depends
from typing import Optional

from app.services.data.market_service import market_service
from app.schemas.market import TokenListResponse, TokenDetailResponse, ExchangeListResponse
from app.core.security import get_current_user_optional
from app.services.data.coingecko_service import coingecko_service
from app.services.data.websocket_manager import manager

router = APIRouter()


@router.get("/tokens", response_model=TokenListResponse)
async def get_tokens_list(
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=100, ge=1, le=250, description="Элементов на странице"),
    sort: Optional[str] = Query(default=None, description="Поле для сортировки (market_cap, volume)")
):
    """
    Получение списка токенов
    
    - **page**: Номер страницы (по умолчанию: 1)
    - **limit**: Элементов на странице (по умолчанию: 100, максимум: 250)
    - **sort**: Поле для сортировки (market_cap, volume)
    """
    try:
        if sort and sort not in ["market_cap", "volume"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверное поле сортировки. Доступные: market_cap, volume"
            )
        
        result = market_service.get_tokens_list(page=page, limit=limit, sort=sort)
        
        if not result.data:
            print(f"[WARNING][Market] - Токены не найдены на странице {page}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR][Market] - Ошибка получения списка бирж: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка бирж"
        )


@router.post("/admin/check-tables")
async def check_existing_tables(
    current_user = Depends(get_current_user_optional)
):
    """
    Проверяет доступность существующих таблиц Liberandum
    
    Проверяет подключение к готовым таблицам без создания тестовых данных
    """
    try:
        result = market_service.create_sample_data()
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][Market] - Ошибка проверки таблиц: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка проверки существующих таблиц"
        )

@router.get("/admin/statistics")
async def get_database_statistics(
    current_user = Depends(get_current_user_optional)
):
    """
    Получает статистику по всем таблицам Liberandum
    
    Показывает количество записей и статус каждой таблицы
    """
    try:
        result = market_service.get_table_statistics()
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][Market] - Ошибка получения статистики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики базы данных"
        )

@router.get("/health")
async def market_health_check():
    """Проверка здоровья Market API"""
    try:
        table_check = market_service.create_sample_data()
        
        tokens_result = market_service.get_tokens_list(limit=1)
        exchanges_result = market_service.get_exchanges_list()
        
        return {
            "status": "healthy",
            "service": "Market Data API",
            "endpoints": {
                "tokens": "/market/tokens",
                "token_detail": "/market/tokens/{token_id}",
                "exchanges": "/market/exchanges"
            },
            "tables_status": table_check.get("tables", {}),
            "data_status": {
                "tokens_available": len(tokens_result.data) > 0,
                "exchanges_available": len(exchanges_result.data) > 0
            },
            "version": "1.0.0",
            "database": "Liberandum Aggregation Tables"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "Market Data API",
            "database": "Liberandum Aggregation Tables"
        }
    except Exception as e:
        print(f"[ERROR][Market] - Ошибка получения списка токенов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка токенов"
        )

@router.get("/tokens/{token_id}", response_model=TokenDetailResponse)
async def get_token_detail(
    token_id: str
):
    """
    Получение детальной информации о токене
    
    - **token_id**: Идентификатор токена (например, "bitcoin", "ethereum")
    """
    try:
        result = market_service.get_token_detail(token_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Токен не найден"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR][Market] - Ошибка получения токена {token_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения информации о токене"
        )



@router.get("/tokens/{token_id}/chart")
async def get_token_chart(
    token_id: str,
    timeframe: str = Query(..., description="Timeframe for chart data"),
    currency: str = Query("usd", description="Currency for price data"),
):
    try:
        valid_timeframes = ["1h", "24h", "7d", "30d", "90d", "1y", "max"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timeframe. Valid options: {valid_timeframes}"
            )
        
        chart_data = await coingecko_service.get_token_chart_data(
            token_id=token_id,
            timeframe=timeframe,
            currency=currency
        )
        
        if not chart_data:
            raise HTTPException(status_code=404, detail="Token not found")
            
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting chart for token {token_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/exchanges", response_model=ExchangeListResponse)
async def get_exchanges_list():

    try:
        result = market_service.get_exchanges_list()
        
        if not result.data:
            print(f"[WARNING][Market] - Биржи не найдены")
        
        return result
        
    except Exception as e:
        print(f"[ERROR][Market] - Ошибка получения списка бирж: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка бирж"
        )