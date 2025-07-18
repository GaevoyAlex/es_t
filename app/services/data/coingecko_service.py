import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
from app.core.config import settings

class CoinGeckoService:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.pro_base_url = "https://pro-api.coingecko.com/api/v3"
        self.timeout = 30.0
        
        self.api_key = getattr(settings, 'COINGECKO_API_KEY', None)
        self.use_pro = bool(self.api_key)
        
        if self.use_pro:
            print(f"[INFO][CoinGecko] - Using Pro API with key")
        else:
            print(f"[WARNING][CoinGecko] - Using free API (rate limited)")
    
    def _get_headers(self) -> Dict[str, str]:

        headers = {
            "Accept": "application/json",
            "User-Agent": "Liberandum-API/1.0"
        }
        
        if self.use_pro and self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
            
        return headers
    
    def _get_base_url(self) -> str:

        return self.pro_base_url if self.use_pro else self.base_url
        
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:

        try:
            base_url = self._get_base_url()
            headers = self._get_headers()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{base_url}{endpoint}", 
                    params=params, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    print(f"[WARNING][CoinGecko] - Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                elif response.status_code == 401:
                    print(f"[ERROR][CoinGecko] - Unauthorized. Check API key")
                    return None
                elif response.status_code == 403:
                    print(f"[ERROR][CoinGecko] - Forbidden. API key may be invalid")
                    return None
                else:
                    print(f"[ERROR][CoinGecko] - HTTP {response.status_code}: {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            print(f"[ERROR][CoinGecko] - Request timeout for {endpoint}")
            return None
        except Exception as e:
            print(f"[ERROR][CoinGecko] - Request failed: {e}")
            return None
    
    def _get_days_from_timeframe(self, timeframe: str) -> str:

        timeframe_mapping = {
            "1h": "1",
            "24h": "1", 
            "7d": "7",
            "30d": "30",
            "90d": "90",
            "1y": "365",
            "max": "max"
        }
        return timeframe_mapping.get(timeframe, "1")
    
    def _get_interval_from_timeframe(self, timeframe: str) -> str:

        if timeframe == "1h":
            return "5m" if self.use_pro else "minutely"
        elif timeframe == "24h":
            return "1h" if self.use_pro else "minutely"
        elif timeframe == "7d":
            return "4h" if self.use_pro else "hourly"
        elif timeframe == "30d":
            return "1d" if self.use_pro else "daily"
        else:
            return "1d" if self.use_pro else "daily"
    
    async def get_token_chart_data(self, token_id: str, timeframe: str, currency: str = "usd") -> Optional[Dict[str, Any]]:

        days = self._get_days_from_timeframe(timeframe)
        interval = self._get_interval_from_timeframe(timeframe)
        
        params = {
            "vs_currency": currency,
            "days": days
        }
        
        if self.use_pro and days != "max":
            params["interval"] = interval
        elif not self.use_pro and days != "1":
            params["interval"] = interval
        
        chart_data = await self._make_request(f"/coins/{token_id}/market_chart", params)
        if not chart_data:
            return None
        
        coin_info = await self._make_request(f"/coins/{token_id}")
        if not coin_info:
            return None
        
        prices = chart_data.get("prices", [])
        market_caps = chart_data.get("market_caps", [])
        volumes = chart_data.get("total_volumes", [])
        
        if not prices:
            return None
        
        price_values = [price[1] for price in prices]
        volume_values = [vol[1] for vol in volumes]
        
        first_price = prices[0][1] if prices else 0
        last_price = prices[-1][1] if prices else 0
        price_change_percentage = ((last_price - first_price) / first_price * 100) if first_price > 0 else 0
        
        statistics = {
            "price_change_percentage": round(price_change_percentage, 2),
            "highest_price": max(price_values) if price_values else 0,
            "lowest_price": min(price_values) if price_values else 0,
            "average_volume": sum(volume_values) / len(volume_values) if volume_values else 0
        }
        
        return {
            "token_id": token_id,
            "symbol": coin_info.get("symbol", "").upper(),
            "name": coin_info.get("name", ""),
            "timeframe": timeframe,
            "currency": currency,
            "data": {
                "prices": prices,
                "market_caps": market_caps,
                "total_volumes": volumes
            },
            "statistics": statistics,
            "updated_at": int(time.time() * 1000),
            "api_source": "pro" if self.use_pro else "free"
        }
    
    async def get_token_current_price(self, token_id: str, currency: str = "usd") -> Optional[Dict[str, Any]]:
        params = {
            "ids": token_id,
            "vs_currencies": currency,
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        
        if self.use_pro:
            params.update({
                "include_last_updated_at": "true",
                "precision": "full"
            })
        
        data = await self._make_request("/simple/price", params)
        if not data or token_id not in data:
            return None
        
        token_data = data[token_id]
        
        coin_info = await self._make_request(f"/coins/{token_id}")
        symbol = coin_info.get("symbol", "").upper() if coin_info else token_id.upper()
        
        return {
            "token_id": token_id,
            "symbol": symbol,
            "price": token_data.get(currency, 0),
            "price_change_24h": token_data.get(f"{currency}_24h_change", 0),
            "volume_24h": token_data.get(f"{currency}_24h_vol", 0),
            "market_cap": token_data.get(f"{currency}_market_cap", 0),
            "timestamp": int(time.time() * 1000),
            "last_updated": token_data.get("last_updated_at") if self.use_pro else None,
            "api_source": "pro" if self.use_pro else "free"
        }

coingecko_service = CoinGeckoService()