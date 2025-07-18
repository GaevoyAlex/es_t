
from fastapi import APIRouter, HTTPException, status, Query
from app.schemas.user import OTPRequest
from app.services.auth.otp_service import generate_and_send_otp, cleanup_expired_otps
from app.crud.user import get_user_by_email

router = APIRouter()

# =============== ПОВТОРНАЯ ОТПРАВКА OTP ===============

@router.post("/resend")
def resend_otp_post(otp_request: OTPRequest):
    """
    Body:
    {
        "email": "user@example.com",
        "otp_type": "registration" | "login"
    }
    """
    user = get_user_by_email(otp_request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    if otp_request.otp_type not in ["registration", "login"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный тип OTP. Используйте 'registration' или 'login'",
        )
    
 
    if otp_request.otp_type == "registration" and user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже подтвержден. OTP для регистрации не нужен",
        )
    
    if otp_request.otp_type == "login" and not user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала подтвердите регистрацию",
        )
    
 
    otp_sent = generate_and_send_otp(otp_request.email, otp_request.otp_type)
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки кода подтверждения",
        )
    
    print(f"[INFO][OTP] - OTP переотправлен для {otp_request.otp_type}: {otp_request.email}")
    return {
        "message": f"Код подтверждения для {otp_request.otp_type} отправлен повторно",
        "email": otp_request.email,
        "otp_type": otp_request.otp_type,
        "note": "Проверьте логи приложения для получения OTP кода"
    }

@router.get("/resend")
def resend_otp_get(
    email: str = Query(..., description="Email пользователя"),
    otp_type: str = Query(..., description="Тип OTP: registration или login")
):
    """
    Повторная отправка OTP кода (GET метод с query параметрами)
    
    URL: /auth/otp/resend?email=user@example.com&otp_type=registration
    """
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    if otp_type not in ["registration", "login"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный тип OTP. Используйте 'registration' или 'login'",
        )
    
 
    if otp_type == "registration" and user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже подтвержден. OTP для регистрации не нужен",
        )
    
    if otp_type == "login" and not user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала подтвердите регистрацию",
        )
    
 
    otp_sent = generate_and_send_otp(email, otp_type)
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки кода подтверждения",
        )
    
    print(f"[INFO][OTP] - OTP переотправлен для {otp_type}: {email}")
    return {
        "message": f"Код подтверждения для {otp_type} отправлен повторно",
        "email": email,
        "otp_type": otp_type,
        "note": "Проверьте логи приложения для получения OTP кода"
    }

@router.post("/resend-registration")
def resend_registration_otp(email: str):
    """
    Специальный метод для повторной отправки OTP при регистрации
    
    Body: "user@example.com" (строка)
    """
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    if user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже подтвержден",
        )
    
 
    otp_sent = generate_and_send_otp(email, "registration")
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки кода подтверждения",
        )
    
    print(f"[INFO][OTP] - OTP для регистрации переотправлен: {email}")
    return {
        "message": "Код подтверждения регистрации отправлен повторно",
        "email": email,
        "otp_type": "registration",
        "note": "Проверьте логи приложения для получения OTP кода"
    }

@router.post("/resend-login")
def resend_login_otp(email: str):
    """
    Специальный метод для повторной отправки OTP при входе
    
    Body: "user@example.com" (строка)
    """
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    if not user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала подтвердите регистрацию",
        )
    
 
    otp_sent = generate_and_send_otp(email, "login")
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки кода подтверждения",
        )
    
    print(f"[INFO][OTP] - OTP для входа переотправлен: {email}")
    return {
        "message": "Код подтверждения входа отправлен повторно",
        "email": email,
        "otp_type": "login",
        "note": "Проверьте логи приложения для получения OTP кода"
    }

# =============== УПРАВЛЕНИЕ И СТАТИСТИКА ===============

@router.get("/status/{email}")
def get_otp_status(email: str):
    """Получить статус OTP для пользователя"""
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    available_types = []
    if not user.get('is_verified', False):
        available_types.append("registration")
    if user.get('is_verified', False):
        available_types.append("login")
    
    return {
        "email": email,
        "is_verified": user.get('is_verified', False),
        "can_request_registration_otp": not user.get('is_verified', False),
        "can_request_login_otp": user.get('is_verified', False),
        "available_otp_types": available_types,
        "user_status": {
            "created_at": user.get('created_at'),
            "auth_provider": user.get('auth_provider', 'local'),
            "is_active": user.get('is_active', True)
        }
    }

# @router.delete("/cleanup")
# def cleanup_expired_otp():
 
#     deleted_count = cleanup_expired_otps()
    
#     return {
#         "message": "Очистка истекших OTP кодов завершена",
#         "deleted_count": deleted_count,
#         "status": "success"
#     }

# @router.get("/test-config")
# def test_otp_config():
#     """Тестирует конфигурацию OTP и email"""
#     from app.services.auth.email_service import test_email_config
#     from app.core.config import settings
    
#     email_config = test_email_config()
    
#     return {
#         "otp_settings": {
#             "expire_minutes": settings.OTP_EXPIRE_MINUTES,
#             "enabled": True
#         },
#         "email_config": email_config,
#         "status": "operational" if email_config.get("smtp_configured") else "email_disabled"
#     }