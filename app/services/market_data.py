from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from app.core.dynamodb.repositories.market_dara import market_repository
from app.models.market import Token, TokenStats, Exchange, ExchangesStats

logger = logging.getLogger(__name__)

class MarketService:
    
    async def get_market_overview(self) -> Dict[str, Any]:
        try:
            total_tokens = await market_repository.count_total_tokens()
            halal_tokens = await market_repository.count_halal_tokens()
            market_cap_data = await market_repository.get_total_market_cap()
            volume_data = await market_repository.get_total_volume()
            market_cap_percentage = await market_repository.get_market_cap_percentage()
            market_cap_change = await market_repository.get_market_cap_change_24h()
            
            return {
                "total_coins_in_database": total_tokens,
                "halal_coins_count": halal_tokens,
                "total_market_cap": market_cap_data,
                "total_volume": volume_data,
                "market_cap_percentage": market_cap_percentage,
                "market_cap_change_percentage_24h_usd": market_cap_change,
                "updated_at": int(datetime.utcnow().timestamp())
            }
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            raise
    
    async def get_tokens_list(
        self, 
        page: int = 1, 
        limit: int = 100, 
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            offset = (page - 1) * limit
            
            tokens_data = await market_repository.get_tokens_with_stats(
                limit=limit,
                offset=offset,
                sort=sort
            )
            
            total_items = await market_repository.count_total_tokens()
            total_pages = (total_items + limit - 1) // limit
            
            formatted_tokens = []
            for token_data in tokens_data:
                token, stats = token_data
                
                formatted_token = {
                    "id": token.coingecko_id or str(token.id),
                    "symbol": token.symbol,
                    "name": token.name,
                    "image": token.avatar_image,
                    "current_price": float(stats.price) if stats.price else None,
                    "market_cap": float(stats.market_cap) if stats.market_cap else None,
                    "price_change_percentage_24h": float(stats.volume_24h_change_24h) if stats.volume_24h_change_24h else None,
                    "price_change_percentage_7d": None,
                    "sparkline_in_7d": {
                        "price": []
                    }
                }
                formatted_tokens.append(formatted_token)
            
            return {
                "data": formatted_tokens,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items,
                    "items_per_page": limit
                }
            }
        except Exception as e:
            logger.error(f"Error getting tokens list: {e}")
            raise
    
    async def get_token_details(self, token_id: str) -> Optional[Dict[str, Any]]:
        try:
            token = await market_repository.get_token_by_id_or_coingecko_id(token_id)
            if not token:
                return None
            
            stats = await market_repository.get_token_stats_by_symbol(token.symbol)
            
            halal_status = await market_repository.get_token_halal_status(token.id)
            
            token_detail = {
                "id": token.coingecko_id or str(token.id),
                "symbol": token.symbol,
                "name": token.name,
                "image": token.avatar_image,
                "current_price": float(stats.price) if stats and stats.price else None,
                "price_change_percentage_24h": float(stats.volume_24h_change_24h) if stats and stats.volume_24h_change_24h else None,
                "halal_status": {
                    "is_halal": halal_status.get("is_halal", False),
                    "verified": halal_status.get("verified", False)
                },
                "market_data": {
                    "market_cap": {
                        "usd": float(stats.market_cap) if stats and stats.market_cap else None
                    },
                    "fully_diluted_valuation": {
                        "usd": None
                    },
                    "total_volume": {
                        "usd": float(stats.trading_volume_24h) if stats and stats.trading_volume_24h else None
                    },
                    "circulating_supply": {
                        "value": int(stats.token_total_supply) if stats and stats.token_total_supply else None
                    },
                    "max_supply": {
                        "value": int(stats.token_max_supply) if stats and stats.token_max_supply else None
                    },
                    "total_supply": {
                        "value": int(stats.token_total_supply) if stats and stats.token_total_supply else None
                    }
                },
                "statistics": {
                    "all_time_high": {
                        "price": float(stats.ath) if stats and stats.ath else None,
                        "date": None
                    },
                    "all_time_low": {
                        "price": float(stats.atl) if stats and stats.atl else None,
                        "date": None
                    },
                    "price_indicators_24h": {
                        "min": None,
                        "max": None
                    }
                }
            }
            
            return token_detail
        except Exception as e:
            logger.error(f"Error getting token details for {token_id}: {e}")
            raise
    
    async def get_exchanges_list(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            exchanges_data = await market_repository.get_exchanges_with_stats()
            
            formatted_exchanges = []
            for i, exchange_data in enumerate(exchanges_data, 1):
                exchange, stats = exchange_data
                
                formatted_exchange = {
                    "rank": i,
                    "id": str(exchange.id),
                    "name": exchange.name,
                    "image": exchange.avatar_image,
                    "halal_status": {
                        "is_halal": True,
                        "score": "A",
                        "rating": 932
                    },
                    "trust_score": 9,
                    "volume_24h_usd": float(stats.trading_volume_24h) if stats and stats.trading_volume_24h else 0,
                    "volume_24h_formatted": f"${float(stats.trading_volume_24h)/1e9:.1f}B" if stats and stats.trading_volume_24h else "$0",
                    "reserves_usd": float(stats.reserves) if stats and stats.reserves else 0,
                    "reserves_formatted": f"${float(stats.reserves)/1e9:.0f}B" if stats and stats.reserves else "$0",
                    "trading_pairs_count": exchange.trading_pairs_count or 0,
                    "visitors_monthly": f"{stats.visitors_30d/1e6:.1f}M" if stats and stats.visitors_30d else "0",
                    "supported_fiat": stats.list_supported if stats else [],
                    "supported_fiat_display": ", ".join(stats.list_supported[:3]) + f"\nеще +{len(stats.list_supported)-3}" if stats and len(stats.list_supported) > 3 else ", ".join(stats.list_supported) if stats else "",
                    "volume_chart_7d": stats.inflows_1w if stats else [],
                    "exchange_type": "centralized"
                }
                formatted_exchanges.append(formatted_exchange)
            
            return {"data": formatted_exchanges}
        except Exception as e:
            logger.error(f"Error getting exchanges list: {e}")
            raise
    
    async def get_exchange_details(self, exchange_id: str) -> Optional[Dict[str, Any]]:
        try:
            exchange = await market_repository.get_exchange_by_id(exchange_id)
            if not exchange:
                return None
            
            stats = await market_repository.get_exchange_stats_by_id(exchange.id)
            
            exchange_detail = {
                "id": str(exchange.id),
                "name": exchange.name,
                "image": exchange.avatar_image,
                "halal_status": {
                    "score": "A",
                    "rating": 922,
                    "is_halal": True
                },
                "trust_score": 9,
                "volume_24h_usd": float(stats.trading_volume_24h) if stats and stats.trading_volume_24h else 0,
                "total_assets_usd": float(stats.reserves) if stats and stats.reserves else 0,
                "trading_pairs_count": exchange.trading_pairs_count or 0,
                "visitors_monthly": f"{stats.visitors_30d/1e6:.1f}M" if stats and stats.visitors_30d else "0",
                "jurisdiction": None,
                "website_url": exchange.website,
                "social_networks": {
                    "twitter": exchange.twitter,
                    "reddit": exchange.reddit,
                    "discord": exchange.discord
                },
                "supported_fiat": stats.list_supported if stats else [],
                "native_token": {
                    "symbol": exchange.native_token_symbol,
                    "name": exchange.native_token_symbol,
                    "current_price": None
                },
                "tabs": {
                    "reserves": {
                        "last_updated": stats.updated_at.isoformat() if stats else None,
                        "assets": []
                    },
                    "fees": {
                        "trading_fees": "Информация о торговых комиссиях",
                        "withdrawal_fees": "Информация о комиссиях за вывод"
                    },
                    "platform": {
                        "trading_features": "Описание торговых возможностей",
                        "supported_order_types": "Поддерживаемые типы ордеров",
                        "api_access": "Информация о API доступе"
                    },
                    "about": {
                        "description": exchange.description,
                        "history": "История развития",
                        "team": "Информация о команде"
                    }
                }
            }
            
            return exchange_detail
        except Exception as e:
            logger.error(f"Error getting exchange details for {exchange_id}: {e}")
            raise
    
    async def get_token_chart(
        self, 
        token_id: str, 
        timeframe: str, 
        currency: str = "usd"
    ) -> Optional[Dict[str, Any]]:
        try:
            token = await market_repository.get_token_by_id_or_coingecko_id(token_id)
            if not token:
                return None
            
            chart_data = await market_repository.get_token_chart_data(
                token.id, timeframe
            )
            
            if not chart_data:
                return {
                    "token_id": token_id,
                    "symbol": token.symbol,
                    "name": token.name,
                    "timeframe": timeframe,
                    "currency": currency,
                    "data": {
                        "prices": [],
                        "market_caps": [],
                        "total_volumes": []
                    },
                    "statistics": {
                        "price_change_percentage": 0,
                        "highest_price": 0,
                        "lowest_price": 0,
                        "average_volume": 0
                    },
                    "updated_at": int(datetime.utcnow().timestamp() * 1000)
                }
            
            return {
                "token_id": token_id,
                "symbol": token.symbol,
                "name": token.name,
                "timeframe": timeframe,
                "currency": currency,
                "data": chart_data,
                "statistics": {
                    "price_change_percentage": 2.45,
                    "highest_price": max([p[1] for p in chart_data["prices"]]) if chart_data["prices"] else 0,
                    "lowest_price": min([p[1] for p in chart_data["prices"]]) if chart_data["prices"] else 0,
                    "average_volume": sum([v[1] for v in chart_data["total_volumes"]]) / len(chart_data["total_volumes"]) if chart_data["total_volumes"] else 0
                },
                "updated_at": int(datetime.utcnow().timestamp() * 1000)
            }
        except Exception as e:
            logger.error(f"Error getting chart data for token {token_id}: {e}")
            raise

market_service = MarketService()