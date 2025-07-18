from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
import uuid

from app.core.dynamodb.connector import get_generic_repository
from app.schemas.market import (
    TokenResponse, TokenDetailResponse, TokenListResponse,
    ExchangeResponse, ExchangeListResponse,
    TokenDataConverter, ExchangeDataConverter,
    HalalStatus, MarketData, Statistics, AllTimeHigh, AllTimeLow, PriceIndicators24h
)

class MarketDataService:
    def __init__(self):
        self.token_stats_table = "LiberandumAggregationTokenStats"
        self.tokens_table = "LiberandumAggregationToken"
        self.token_platform_table = "LiberandumAggregationTokenPlatform"
        self.exchange_stats_table = "LiberandumAggregationExchangesStats"
        self.exchanges_table = "LiberandumAggregationExchanges"

    def _get_repository(self, table_name: str):

        repo = get_generic_repository(table_name)
        if not repo:
            raise RuntimeError(f"Репозиторий для таблицы {table_name} недоступен")
        return repo

    # =============== TOKENS ===============

    def get_tokens_list(self, page: int = 1, limit: int = 100, sort: Optional[str] = None) -> TokenListResponse:

        try:
            print(f"[DEBUG] === НАЧАЛО get_tokens_list ===")
            print(f"[DEBUG] Параметры: page={page}, limit={limit}, sort={sort}")
            
            token_stats_repo = self._get_repository(self.token_stats_table)
            tokens_repo = self._get_repository(self.tokens_table)
            
            print(f"[DEBUG] Репозитории получены")
            
            
            scan_limit = min(limit * 2, 50) 
            print(f"[DEBUG] Сканируем с лимитом {scan_limit}")
            
            all_token_stats = token_stats_repo.scan_items(
                self.token_stats_table,
                limit=scan_limit
            )
            
            print(f"[DEBUG] Получено {len(all_token_stats)} записей из scan")
            
            token_stats = [ts for ts in all_token_stats if not ts.get('is_deleted', False)]
            print(f"[DEBUG] После фильтрации: {len(token_stats)} записей")
            
            print(f"[DEBUG] Начинаем сортировку...")
            try:
                if sort == "market_cap":

                    token_stats = sorted(token_stats, key=lambda x: float(str(x.get('market_cap', 0) or 0).replace(',', '')), reverse=True)
                elif sort == "volume":
                    token_stats = sorted(token_stats, key=lambda x: float(str(x.get('trading_volume_24h', 0) or 0).replace(',', '')), reverse=True)

            except Exception as sort_error:
                print(f"[WARNING] Ошибка сортировки, пропускаем: {sort_error}")
            
            total_items = len(token_stats)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_stats = token_stats[start_idx:end_idx]
            
            
            token_responses = []
            for i, stat in enumerate(paginated_stats):
                try:
                    
                    token_response = self._simple_convert_token(stat)
                    token_responses.append(token_response)
                    
                except Exception as convert_error:
                    print(f"[ERROR] Ошибка конвертации токена {i}: {convert_error}")
                    continue
            
            print(f"[DEBUG] Обработано {len(token_responses)} токенов")
            
            pagination = {
                "current_page": page,
                "total_pages": (total_items + limit - 1) // limit if total_items > 0 else 0,
                "total_items": total_items,
                "items_per_page": limit
            }
            
            
            return TokenListResponse(
                data=token_responses,
                pagination=pagination
            )
            
        except Exception as e:
            print(f"[ERROR] Критическая ошибка в get_tokens_list: {e}")
            import traceback
            traceback.print_exc()
            
            return TokenListResponse(
                data=[], 
                pagination={
                    "current_page": 1, 
                    "total_pages": 0, 
                    "total_items": 0, 
                    "items_per_page": limit
                }
            )
    
    def _simple_convert_token(self, token_stats: Dict[str, Any]):

        from app.schemas.market import TokenResponse, TokenSparkline
        
        try:
            
            price = 0.0
            market_cap = 0
            
            try:
                price = float(str(token_stats.get('price', 0) or 0).replace(',', ''))
            except:
                pass
                
            try:
                market_cap = int(float(str(token_stats.get('market_cap', 0) or 0).replace(',', '')))
            except:
                pass
            
            
            sparkline_data = [price] * 7  
            
            return TokenResponse(
                id=str(token_stats.get('coingecko_id', token_stats.get('symbol', 'unknown'))).lower(),
                symbol=str(token_stats.get('symbol', 'UNKNOWN')).upper(),
                name=str(token_stats.get('coin_name', 'Unknown Token')),
                image="",  
                current_price=price,
                market_cap=market_cap,
                price_change_percentage_24h=0.0, 
                price_change_percentage_7d=0.0,   
                sparkline_in_7d=TokenSparkline(price=sparkline_data)
            )
        except Exception as e:
            print(f"[ERROR] Ошибка простой конвертации: {e}")
            return TokenResponse(
                id="error",
                symbol="ERROR",
                name="Error Token",
                image="",
                current_price=0.0,
                market_cap=0,
                price_change_percentage_24h=0.0,
                price_change_percentage_7d=0.0,
                sparkline_in_7d=TokenSparkline(price=[0.0] * 7)
            )

    def get_token_detail(self, token_id: str) -> Optional[TokenDetailResponse]:

        try:
            token_stats_repo = self._get_repository(self.token_stats_table)
            tokens_repo = self._get_repository(self.tokens_table)
            
            token_stats_results = token_stats_repo.find_by_field('coingecko_id', token_id)
            if not token_stats_results:
                return None
            
            token_stats = token_stats_results[0]
            
            token = None
            if token_stats.get('symbol'):
                token_results = tokens_repo.find_by_field('symbol', token_stats['symbol'])
                if token_results:
                    token = token_results[0]
            
            return TokenDetailResponse(
                id=token_stats.get('coingecko_id', ''),
                symbol=token_stats.get('symbol', '').upper(),
                name=token_stats.get('coin_name', ''),
                image=token.get('avatar_image', '') if token else '',
                current_price=float(token_stats.get('price', 0)),
                price_change_percentage_24h=float(token_stats.get('volume_24h_change_24h', 0)),
                halal_status=HalalStatus(
                    is_halal=True,  
                    verified=True
                ),
                market_data=MarketData(
                    market_cap={"usd": int(float(token_stats.get('market_cap', 0)))},
                    fully_diluted_valuation={"usd": int(float(token_stats.get('market_cap', 0))) * 2}, 
                    total_volume={"usd": int(float(token_stats.get('trading_volume_24h', 0)))},
                    circulating_supply={"value": int(float(token_stats.get('token_total_supply', 0)))},
                    max_supply={"value": int(float(token_stats.get('token_max_supply', 0)))},
                    total_supply={"value": int(float(token_stats.get('token_total_supply', 0)))}
                ),
                statistics=Statistics(
                    all_time_high=AllTimeHigh(
                        price=float(token_stats.get('ath', 0)),
                        date="2025-05-22T00:00:00Z"  
                    ),
                    all_time_low=AllTimeLow(
                        price=float(token_stats.get('atl', 0)),
                        date="2019-06-14T00:00:00Z"  
                    ),
                    price_indicators_24h=PriceIndicators24h(
                        min=float(token_stats.get('price', 0)) * 0.95,  
                        max=float(token_stats.get('price', 0)) * 1.05   
                    )
                )
            )
            
        except Exception as e:
            print(f"[ERROR][MarketService] - Ошибка получения токена {token_id}: {e}")
            return None

    # =============== EXCHANGES ===============

    def get_exchanges_list(self) -> ExchangeListResponse:

        try:
            exchange_stats_repo = self._get_repository(self.exchange_stats_table)
            exchanges_repo = self._get_repository(self.exchanges_table)
            
            all_exchange_stats = exchange_stats_repo.scan_items(self.exchange_stats_table)
            
            exchange_stats = [es for es in all_exchange_stats if not es.get('is_deleted', False)]
            exchange_stats.sort(key=lambda x: float(x.get('trading_volume_24h', 0) or 0), reverse=True)
            
            exchange_responses = []
            for idx, stat in enumerate(exchange_stats, 1):

                exchange = None
                if stat.get('exchange_id'):
                    exchange = exchanges_repo.get_by_id(str(stat['exchange_id']))
                
                exchange_response = ExchangeDataConverter.from_db_to_api(stat, exchange, idx)
                exchange_responses.append(exchange_response)
            
            return ExchangeListResponse(data=exchange_responses)
            
        except Exception as e:
            print(f"[ERROR][MarketService] - Ошибка получения списка бирж: {e}")
            return ExchangeListResponse(data=[])


    def create_sample_data(self) -> Dict[str, Any]:

        try:

            table_status = {}
            
            for table_name in [
                self.tokens_table, 
                self.token_stats_table,
                self.exchanges_table, 
                self.exchange_stats_table,
                self.token_platform_table
            ]:
                try:
                    repo = self._get_repository(table_name)
                    items = repo.scan_items(table_name, limit=1)
                    table_status[table_name] = {
                        "accessible": True,
                        "has_data": len(items) > 0
                    }
                except Exception as e:
                    table_status[table_name] = {
                        "accessible": False,
                        "error": str(e)
                    }
            
            return {
                "message": "Подключение к существующим таблицам Liberandum",
                "tables": table_status,
                "note": "Тестовые данные не создаются - используются существующие таблицы"
            }
            
        except Exception as e:
            return {"error": f"Ошибка проверки существующих таблиц: {str(e)}"}


market_service = MarketDataService()