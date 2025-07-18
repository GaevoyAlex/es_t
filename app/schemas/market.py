from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal

# Token Response Schemas
class TokenSparkline(BaseModel):
    price: List[float]

class TokenResponse(BaseModel):
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    market_cap: int
    price_change_percentage_24h: float
    price_change_percentage_7d: float
    sparkline_in_7d: TokenSparkline

class HalalStatus(BaseModel):
    is_halal: bool
    verified: bool

class MarketData(BaseModel):
    market_cap: Dict[str, int]
    fully_diluted_valuation: Dict[str, int]
    total_volume: Dict[str, int]
    circulating_supply: Dict[str, Union[int, float]]
    max_supply: Dict[str, Union[int, float]]
    total_supply: Dict[str, Union[int, float]]

class AllTimeHigh(BaseModel):
    price: float
    date: str

class AllTimeLow(BaseModel):
    price: float
    date: str

class PriceIndicators24h(BaseModel):
    min: float
    max: float

class Statistics(BaseModel):
    all_time_high: AllTimeHigh
    all_time_low: AllTimeLow
    price_indicators_24h: PriceIndicators24h

class TokenDetailResponse(BaseModel):
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    price_change_percentage_24h: float
    halal_status: HalalStatus
    market_data: MarketData
    statistics: Statistics

class TokenListResponse(BaseModel):
    data: List[TokenResponse]
    pagination: Dict[str, int]

# Exchange Response Schemas
class ExchangeHalalStatus(BaseModel):
    is_halal: bool
    score: str
    rating: int

class ExchangeResponse(BaseModel):
    rank: int
    id: str
    name: str
    image: str
    halal_status: ExchangeHalalStatus
    trust_score: int
    volume_24h_usd: Union[int, float]  
    volume_24h_formatted: str
    reserves_usd: Union[int, float]    
    reserves_formatted: str
    trading_pairs_count: int
    visitors_monthly: str
    supported_fiat: List[str]
    supported_fiat_display: str
    volume_chart_7d: List[Union[int, float]] 
    exchange_type: str

class ExchangeListResponse(BaseModel):
    data: List[ExchangeResponse]

# Pagination Schema
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 100
    sort: Optional[str] = None

class TokenDataConverter(BaseModel):
    @staticmethod
    def from_db_to_api(token_stats: Dict[str, Any], token: Dict[str, Any] = None) -> TokenResponse:

        sparkline_data = [
            float(token_stats.get('price', 0)) * 0.98,
            float(token_stats.get('price', 0)) * 0.99,
            float(token_stats.get('price', 0)) * 1.01,
            float(token_stats.get('price', 0)) * 1.02,
            float(token_stats.get('price', 0)) * 0.97,
            float(token_stats.get('price', 0)) * 1.03,
            float(token_stats.get('price', 0))
        ]
        
        return TokenResponse(
            id=token_stats.get('coingecko_id', ''),
            symbol=token_stats.get('symbol', '').upper(),
            name=token_stats.get('coin_name', ''),
            image=token.get('avatar_image', '') if token else '',
            current_price=float(token_stats.get('price', 0)),
            market_cap=int(float(token_stats.get('market_cap', 0))),
            price_change_percentage_24h=float(token_stats.get('volume_24h_change_24h', 0)),
            price_change_percentage_7d=2.5,  # Placeholder
            sparkline_in_7d=TokenSparkline(price=sparkline_data)
        )

class ExchangeDataConverter(BaseModel):
    @staticmethod
    def from_db_to_api(exchange_stats: Dict[str, Any], exchange: Dict[str, Any] = None, rank: int = 1) -> ExchangeResponse:

        try:

            volume_24h = 0
            try:
                volume_24h_str = str(exchange_stats.get('trading_volume_24h', 0) or 0)
                volume_24h = float(volume_24h_str.replace(',', ''))
            except (ValueError, TypeError):
                volume_24h = 0
            
            
            reserves = 0
            try:
                reserves_str = str(exchange_stats.get('reserves', 0) or 0)
                reserves = float(reserves_str.replace(',', ''))
            except (ValueError, TypeError):
                reserves = 0
            
            volume_chart = []
            for multiplier in [0.9, 1.1, 0.95, 1.05, 0.98, 1.02, 1.0]:
                chart_value = volume_24h * multiplier
                volume_chart.append(chart_value)  
            
            return ExchangeResponse(
                rank=rank,
                id=str(exchange_stats.get('name', 'unknown')).lower().replace(' ', '_'),
                name=str(exchange_stats.get('name', 'Unknown Exchange')),
                image=str(exchange.get('avatar_image', '') if exchange else ''),
                halal_status=ExchangeHalalStatus(
                    is_halal=True,  
                    score="A",
                    rating=932
                ),
                trust_score=9, 
                volume_24h_usd=volume_24h,  
                volume_24h_formatted=f"${volume_24h / 1_000_000_000:.1f}B" if volume_24h > 1_000_000_000 else f"${volume_24h / 1_000_000:.1f}M",
                reserves_usd=reserves,      
                reserves_formatted=f"${reserves / 1_000_000_000:.0f}B" if reserves > 1_000_000_000 else f"${reserves / 1_000_000:.0f}M",
                trading_pairs_count=int(exchange_stats.get('coins_count', 0) or 0),
                visitors_monthly=f"{exchange_stats.get('visitors_30d', 0) or 0}M",
                supported_fiat=exchange_stats.get('list_supported', [])[:3] if exchange_stats.get('list_supported') else [],
                supported_fiat_display=", ".join(exchange_stats.get('list_supported', [])[:3]) + (f"\nещё +{len(exchange_stats.get('list_supported', [])) - 3}" if len(exchange_stats.get('list_supported', [])) > 3 else ""),
                volume_chart_7d=volume_chart,  
                exchange_type="centralized"  
            )
        except Exception as e:
            print(f"[ERROR] Ошибка конвертации биржи: {e}")
            
            return ExchangeResponse(
                rank=rank,
                id="error",
                name="Error Exchange", 
                image="",
                halal_status=ExchangeHalalStatus(is_halal=False, score="F", rating=0),
                trust_score=0,
                volume_24h_usd=0,
                volume_24h_formatted="$0",
                reserves_usd=0,
                reserves_formatted="$0",
                trading_pairs_count=0,
                visitors_monthly="0",
                supported_fiat=[],
                supported_fiat_display="",
                volume_chart_7d=[0.0] * 7,
                exchange_type="unknown"
            )