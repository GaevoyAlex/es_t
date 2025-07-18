import random
import string
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.core.dynamodb import get_otp_repository
from .email_service import send_otp_email

def get_repository():

    repo = get_otp_repository()
    if not repo:
        raise RuntimeError(f"Репозиторий OTP недоступен")
    return repo

def generate_otp_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

def generate_and_send_otp(email: str, otp_type: str) -> bool:

    try:
        repo = get_repository()
        
        deleted_count = repo.delete_old_otps_for_email(email, otp_type)
        if deleted_count > 0:
            print(f"[INFO][OTP] - Удалены старые OTP коды: {deleted_count}")
        
        otp_code = generate_otp_code()
        expires_at = (datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat()
        
        otp_data = {
            'email': email,
            'otp_code': otp_code,
            'otp_type': otp_type,
            'expires_at': expires_at
        }
        
        db_otp = repo.create_otp(otp_data)
        
        email_sent = send_otp_email(email, otp_code, otp_type)
        
        if email_sent:
            print(f"[INFO][OTP] - OTP код отправлен на {email}, тип: {otp_type}")
            return True
        else:
            print(f"[ERROR][OTP] - Ошибка отправки OTP на {email}")
            return False
            
    except Exception as e:
        print(f"[ERROR][OTP] - Ошибка при генерации и отправке OTP: {e}")
        return False

def verify_otp_code(email: str, otp_code: str, otp_type: str) -> bool:

    try:
        repo = get_repository()
        
        otp_record = repo.get_valid_otp(email, otp_code, otp_type)
        
        if not otp_record:
            print(f"[INFO][OTP] - OTP код не найден или истек для {email}")
            return False
        
        success = repo.mark_otp_as_used(otp_record['id'])
        
        if success:
            print(f"[INFO][OTP] - OTP код успешно проверен для {email}")
            return True
        else:
            print(f"[ERROR][OTP] - Ошибка при обновлении OTP статуса для {email}")
            return False
        
    except Exception as e:
        print(f"[ERROR][OTP] - Ошибка при проверке OTP: {e}")
        return False

def cleanup_expired_otps() -> int:

    try:
        repo = get_repository()
        deleted_count = repo.cleanup_expired_otps()
        return deleted_count
        
    except Exception as e:
        print(f"[ERROR][OTP] - Ошибка при очистке истекших OTP: {e}")
        return 0

def resend_otp(email: str, otp_type: str) -> bool:

    return generate_and_send_otp(email, otp_type)
