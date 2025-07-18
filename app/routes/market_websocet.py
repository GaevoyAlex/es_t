from fastapi import APIRouter, WebSocket
from app.services.data.market_manager import handle_websocket_connection

router = APIRouter()

@router.websocket("/tokens/{token_id}/price")
async def websocket_price_updates(websocket: WebSocket, token_id: str):
    await handle_websocket_connection(websocket, token_id)