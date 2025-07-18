import httpx
from datetime import timedelta
from typing import Dict, Any, Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import get_user_by_email, create_or_update_google_user, create_tokens_for_user

async def get_google_token(code: str) -> Optional[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        }
        
        try:
            response = await client.post(token_url, data=data)
            print(f"Статус ответа Google OAuth: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Ошибка Google OAuth: {response.text}")
                return None
            
            response_json = response.json()
            print("Токен успешно получен от Google")
            return response_json
        except Exception as e:
            print(f"Исключение при запросе токена: {e}")
            return None

async def get_google_user_info(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        print("Ошибка: передан пустой токен")
        return None

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"Ошибка получения данных пользователя: {response.text}")
            return None

        user_info = response.json()
        print(f"Данные пользователя получены: {user_info.get('email')}")
        return user_info

async def authenticate_google_user(code: str) -> Optional[Dict[str, Any]]:
    if not code:
        print("Ошибка: код авторизации пустой")
        return None

    try:
        token_data = await get_google_token(code)
        if not token_data:
            return None

        access_token = token_data["access_token"]
        user_info = await get_google_user_info(access_token)

        if not user_info:
            return None

        return await _create_jwt_for_user(user_info)

    except Exception as e:
        print(f"Ошибка аутентификации Google: {e}")
        return None

async def authenticate_google_user_with_credential(credential: str) -> Optional[Dict[str, Any]]:
    if not credential:
        print("Ошибка: ID token пустой")
        return None
    
    try:
        id_info = id_token.verify_oauth2_token(
            credential, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        print(f"ID токен успешно верифицирован для: {id_info.get('email')}")
        
        user_info = {
            "email": id_info.get("email"),
            "name": id_info.get("name"),
            "given_name": id_info.get("given_name"),
            "family_name": id_info.get("family_name"),
            "picture": id_info.get("picture")
        }
        
        return await _create_jwt_for_user(user_info)
        
    except ValueError as e:
        print(f"Недействительный ID токен: {e}")
        return None
    except Exception as e:
        print(f"Ошибка аутентификации с ID token: {e}")
        return None

async def _create_jwt_for_user(user_info: Dict[str, Any]) -> Dict[str, Any]:
    email = user_info["email"]
    
    db_user = get_user_by_email(email)
    
    if not db_user:
        print(f"Создаем нового Google пользователя: {email}")
        db_user = create_or_update_google_user(
            email=email,
            name=user_info.get("name", email.split("@")[0]),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name")
        )
    else:
        print(f"Google пользователь уже существует: {email}")
        db_user = create_or_update_google_user(
            email=email,
            name=user_info.get("name", db_user.get("name", "")),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name")
        )
    
    access_token, refresh_token = create_tokens_for_user(db_user['id'])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": db_user
    }