 

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
     
    PROJECT_NAME: str = "FastAPI Auth App"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS DynamoDB настройки
    AWS_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = "" 
    AWS_ENDPOINT_URL: str = ""  
    
    # Названия таблиц DynamoDB
    DYNAMODB_USERS_TABLE: str = ""
    DYNAMODB_OTP_TABLE: str = ""
    
    # Google OAuth настройки
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = "l"
    GOOGLE_REDIRECT_URI: str = ""
    
    # OTP настройки
    OTP_EXPIRE_MINUTES: int = 10
    
    # Email настройки
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    COINGECKO_API_KEY: str = ""
    COINGECKO_PRO_ENABLED: bool = False

    # Режим разработки
    DEVELOPMENT_MODE: bool = True
    USE_LOCALSTACK: bool = False
    
    @property
    def is_localstack(self) -> bool:

        return bool(self.AWS_ENDPOINT_URL and "localhost" in self.AWS_ENDPOINT_URL)
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()