from .user import UserRepository
from app.core.dynamodb.repositories.otp import OTPRepository  
from .generic import GenericRepository

__all__ = [
    'UserRepository',
    'OTPRepository',
    'GenericRepository'
]