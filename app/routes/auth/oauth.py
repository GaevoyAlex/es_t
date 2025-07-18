 
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.schemas.token import Token
from app.schemas.user import GoogleAuthRequest
from app.services.auth.auth_service import authenticate_google_user, authenticate_google_user_with_credential

router = APIRouter()

@router.get("/google/login")
def login_google():

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth не настроен",
        )
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    print(f"[INFO][OAUTH] - Перенаправление на Google OAuth: {settings.GOOGLE_REDIRECT_URI}")
    return RedirectResponse(google_auth_url)

@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Callback для обработки ответа от Google OAuth
    Используется при редиректе после авторизации в браузере
    """
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    
    if error:
        print(f"[ERROR][OAUTH] - Google OAuth ошибка: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка Google OAuth: {error}",
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отсутствует код авторизации от Google",
        )
    
    print(f"[INFO][OAUTH] - Получен код авторизации от Google")
    
 
    auth_result = await authenticate_google_user(code)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации через Google",
        )
    
    print(f"[INFO][OAUTH] - Google аутентификация успешна: {auth_result['user']['email']}")
    
    return {
        "message": "Успешная аутентификация через Google",
        "access_token": auth_result["access_token"],
        "token_type": "bearer",
        "user": {
            "id": auth_result["user"]["id"],
            "email": auth_result["user"]["email"],
            "name": auth_result["user"]["name"],
            "auth_provider": auth_result["user"]["auth_provider"]
        }
    }

@router.post("/google/auth", response_model=Token)
async def auth_google(google_auth: GoogleAuthRequest):
    """
    Аутентификация через Google OAuth для API клиентов
    Поддерживает как authorization code, так и ID token
    """
    print(f"[INFO][OAUTH] - Получен запрос на Google аутентификацию")
    
    if not google_auth.credential and not google_auth.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Требуется код авторизации (code) или credential (ID token)",
        )
    
    auth_result = None
    
 
    if google_auth.credential:
        print(f"[INFO][OAUTH] - Используем credential (ID token) для аутентификации")
        auth_result = await authenticate_google_user_with_credential(google_auth.credential)
    
 
    elif google_auth.code:
        print(f"[INFO][OAUTH] - Используем authorization code для аутентификации")
        auth_result = await authenticate_google_user(google_auth.code)
    
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации через Google",
        )
    
    print(f"[INFO][OAUTH] - Google API аутентификация успешна: {auth_result['user']['email']}")
    
    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer"
    }

@router.get("/google/status")
def google_oauth_status():
    """Статус конфигурации Google OAuth"""
    is_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    
    return {
        "enabled": is_configured,
        "client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(settings.GOOGLE_CLIENT_SECRET),
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "endpoints": {
            "login": "/auth/oauth/google/login",
            "callback": "/auth/oauth/google/callback", 
            "api_auth": "/auth/oauth/google/auth"
        },
        "setup_instructions": [
            "1. Создайте проект в Google Cloud Console",
            "2. Включите Google+ API",
            "3. Создайте OAuth 2.0 credentials",
            "4. Добавьте redirect URI в настройки",
            "5. Установите GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET в .env"
        ] if not is_configured else None
    }

@router.post("/google/revoke")
async def revoke_google_token(token: str):
    """
    Отзыв Google токена (выход из Google аккаунта)
    """
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token}
            )
            
            if response.status_code == 200:
                print(f"[INFO][OAUTH] - Google токен успешно отозван")
                return {"message": "Google токен успешно отозван"}
            else:
                print(f"[ERROR][OAUTH] - Ошибка отзыва Google токена: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ошибка отзыва Google токена"
                )
    except Exception as e:
        print(f"[ERROR][OAUTH] - Исключение при отзыве токена: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отзыве Google токена"
        )