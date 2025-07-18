# from fastapi import APIRouter, HTTPException, Query, Depends
# from typing import Optional, List, Dict, Any
# from decimal import Decimal
# from uuid import UUID
# import logging

# from app.models.market import Token, TokenStats, Exchange, ExchangesStats
# from app.services.data.market_service import market_service
# from app.models.user import User

# logger = logging.getLogger(__name__)
# router = APIRouter()

# @router.get("/overview")
# async def get_market_overview(
# ):
#     try:
#         overview_data = await market_service.get_market_overview()
#         return overview_data
#     except Exception as e:
#         logger.error(f"Error getting market overview: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/tokens")
# async def get_tokens_list(
#     page: int = Query(1, ge=1, description="Page number"),
#     limit: int = Query(100, ge=1, le=250, description="Items per page"),
#     sort: Optional[str] = Query(None, description="Sort field"),
# ):
#     try:
#         tokens_data = await market_service.get_tokens_list(
#             page=page,
#             limit=limit,
#             sort=sort
#         )
#         return tokens_data
#     except Exception as e:
#         logger.error(f"Error getting tokens list: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/tokens/{token_id}")
# async def get_token_details(
#     token_id: str,
# ):
#     try:
#         token_data = await market_service.get_token_details(token_id)
#         if not token_data:
#             raise HTTPException(status_code=404, detail="Token not found")
#         return token_data
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting token details for {token_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/exchanges")
# async def get_exchanges_list(
# ):
#     try:
#         exchanges_data = await market_service.get_exchanges_list()
#         return exchanges_data
#     except Exception as e:
#         logger.error(f"Error getting exchanges list: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/exchanges/{exchange_id}")
# async def get_exchange_details(
#     exchange_id: str,
# ):
#     try:
#         exchange_data = await market_service.get_exchange_details(exchange_id)
#         if not exchange_data:
#             raise HTTPException(status_code=404, detail="Exchange not found")
#         return exchange_data
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting exchange details for {exchange_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/tokens/{token_id}/chart")
# async def get_token_chart(
#     token_id: str,
#     timeframe: str = Query(..., description="Timeframe for chart data"),
#     currency: str = Query("usd", description="Currency for price data"),
# ):
#     try:
#         valid_timeframes = ["1h", "24h", "7d", "30d", "90d", "1y", "max"]
#         if timeframe not in valid_timeframes:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid timeframe. Valid options: {valid_timeframes}"
#             )
        
#         chart_data = await market_service.get_token_chart(
#             token_id=token_id,
#             timeframe=timeframe,
#             currency=currency
#         )
        
#         if not chart_data:
#             raise HTTPException(status_code=404, detail="Token not found")
            
#         return chart_data
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting chart for token {token_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")