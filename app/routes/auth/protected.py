from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserResponse, UserUpdate
from app.core.security import get_current_user, get_current_user_optional
from app.crud.user import update_user, deactivate_user, activate_user, change_user_password, logout_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    print(f"[INFO][PROTECTED] - Запрос профиля пользователя: {current_user['email']}")
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user = Depends(get_current_user)
):
    print(f"[INFO][PROTECTED] - Обновление профиля: {current_user['email']}")
    
    updates = {}
    if user_update.name is not None:
        updates['name'] = user_update.name
    if user_update.first_name is not None:
        updates['first_name'] = user_update.first_name
    if user_update.last_name is not None:
        updates['last_name'] = user_update.last_name
    
    if not updates:
        return current_user
    
    updated_user = update_user(current_user['id'], **updates)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления профиля"
        )
    
    print(f"[INFO][PROTECTED] - Профиль обновлен: {current_user['email']}")
    return updated_user

@router.patch("/me/name")
async def update_user_name(
    name: str,
    current_user = Depends(get_current_user)
):
    updated_user = update_user(current_user['id'], name=name)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления имени"
        )
    
    return {"message": "Имя обновлено", "name": name}

@router.post("/me/deactivate")
async def deactivate_current_user(current_user = Depends(get_current_user)):
    deactivated_user = deactivate_user(current_user['id'])
    if not deactivated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка деактивации аккаунта"
        )
    
    print(f"[INFO][PROTECTED] - Аккаунт деактивирован: {current_user['email']}")
    return {
        "message": "Аккаунт деактивирован",
        "email": current_user['email'],
        "status": "deactivated"
    }

@router.post("/me/activate")
async def activate_current_user(current_user = Depends(get_current_user)):
    activated_user = activate_user(current_user['id'])
    if not activated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка активации аккаунта"
        )
    
    print(f"[INFO][PROTECTED] - Аккаунт активирован: {current_user['email']}")
    return {
        "message": "Аккаунт активирован",
        "email": current_user['email'],
        "status": "active"
    }

@router.post("/me/change-password")
async def change_current_user_password(
    new_password: str,
    current_user = Depends(get_current_user)
):
    if current_user.get('auth_provider') == 'google':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google пользователи не могут изменять пароль через эту систему"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен содержать минимум 8 символов"
        )
    
    updated_user = change_user_password(current_user['id'], new_password)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка изменения пароля"
        )
    
    print(f"[INFO][PROTECTED] - Пароль изменен: {current_user['email']}")
    return {
        "message": "Пароль успешно изменен",
        "email": current_user['email']
    }

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    success = logout_user(current_user['id'])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выходе из системы"
        )
    
    print(f"[INFO][PROTECTED] - Пользователь вышел из системы: {current_user['email']}")
    return {
        "message": "Успешный выход из системы",
        "email": current_user['email']
    }

@router.post("/logout-all")
async def logout_all_sessions(current_user = Depends(get_current_user)):
    success = logout_user(current_user['id'])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выходе из всех сессий"
        )
    
    print(f"[INFO][PROTECTED] - Выход из всех сессий: {current_user['email']}")
    return {
        "message": "Выход из всех сессий выполнен",
        "email": current_user['email']
    }

@router.get("/sessions")
async def get_user_sessions(current_user = Depends(get_current_user)):
    has_tokens = bool(current_user.get('access_token') and current_user.get('refresh_token'))
    
    return {
        "current_session": {
            "user_id": current_user['id'],
            "email": current_user['email'],
            "auth_provider": current_user.get('auth_provider', 'local'),
            "last_login": current_user.get('updated_at'),
            "active": has_tokens,
            "role": current_user.get('role', 'user')
        },
        "total_sessions": 1 if has_tokens else 0
    }

@router.get("/me/stats")
async def get_user_stats(current_user = Depends(get_current_user)):
    from datetime import datetime
    
    created_at = current_user.get('created_at')
    if created_at:
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            account_age_days = (datetime.utcnow() - created_date).days
        except:
            account_age_days = 0
    else:
        account_age_days = 0
    
    return {
        "user_info": {
            "id": current_user['id'],
            "email": current_user['email'],
            "name": current_user['name'],
            "is_verified": current_user.get('is_verified', False),
            "is_active": current_user.get('is_active', True),
            "auth_provider": current_user.get('auth_provider', 'local'),
            "role": current_user.get('role', 'user')
        },
        "account_stats": {
            "created_at": created_at,
            "account_age_days": account_age_days,
            "last_updated": current_user.get('updated_at')
        },
        "security_info": {
            "has_password": bool(current_user.get('hashed_password')),
            "is_google_user": current_user.get('auth_provider') == 'google',
            "email_verified": current_user.get('is_verified', False),
            "has_active_tokens": bool(current_user.get('access_token') and current_user.get('refresh_token'))
        }
    }