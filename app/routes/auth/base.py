from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.crud.user import authenticate_user, create_user, get_user_by_email, get_user_by_name, create_tokens_for_user, refresh_access_token
from app.schemas.token import Token, TokenRefresh
from app.schemas.user import UserCreate, UserLogin, UserResponse, OTPVerification
from app.core.security import create_access_token
from app.services.auth.otp_service import generate_and_send_otp, verify_otp_code

router = APIRouter()

@router.post("/register")
def register_user(user_in: UserCreate):
    if get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    
    if get_user_by_name(user_in.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )
    
    user = create_user(user_in, is_verified=False)
    
    otp_sent = generate_and_send_otp(user['email'], "registration")
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки кода подтверждения",
        )
    
    print(f"[INFO][AUTH] - OTP отправлен для регистрации: {user['email']}")
    return {
        "message": "Пользователь зарегистрирован. Проверьте email для подтверждения",
        "email": user['email'],
        "requires_verification": True,
        "note": "Если email не настроен, проверьте логи приложения для получения OTP кода"
    }

@router.post("/verify-registration", response_model=Token)
def verify_registration(otp_data: OTPVerification):
    user = get_user_by_email(otp_data.email)
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
    
    is_valid = verify_otp_code(otp_data.email, otp_data.otp_code, "registration")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший код подтверждения",
        )
    
    from app.crud.user import verify_user_email
    updated_user = verify_user_email(user['id'])
    
    access_token, refresh_token = create_tokens_for_user(updated_user['id'])
    
    print(f"[INFO][AUTH] - Пользователь подтвержден и получил токены: {user['email']}")
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login")
def login_for_access_token(user_in: UserLogin):
    user = authenticate_user(user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден. Пожалуйста, подтвердите регистрацию",
        )
    
    otp_sent = generate_and_send_otp(user['email'], "login")
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки кода подтверждения",
        )
    
    print(f"[INFO][AUTH] - OTP отправлен для входа: {user['email']}")
    return {
        "message": "Код подтверждения отправлен на email",
        "email": user['email'],
        "requires_otp": True,
    }

@router.post("/verify-login", response_model=Token)
def verify_login_otp(otp_data: OTPVerification):
    user = get_user_by_email(otp_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    if not user.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден",
        )
    
    is_valid = verify_otp_code(otp_data.email, otp_data.otp_code, "login")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший код подтверждения",
        )
    
    access_token, refresh_token = create_tokens_for_user(user['id'])
    
    print(f"[INFO][AUTH] - Пользователь успешно вошел: {user['email']}")
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh):
    tokens = refresh_access_token(token_data.refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh token",
        )
    
    access_token, refresh_token = tokens
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }