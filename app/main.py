from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Liberandun API",
    description="API для работы с криптовалютными данными, биржами и токенами",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:3000"
    ],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Crypto Market API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "auth": "/auth",
            "market": "/market",
            "data": "/data"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "auth": "operational",
            "market": "operational", 
            "database": "operational"
        }
    }

try:
    
    from app.routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

    from app.routes.api.markets import router as market_router
    app.include_router(market_router, prefix="/market", tags=["Market Data"])

    from app.routes.api.data import router as data_router
    app.include_router(data_router, prefix="/data", tags=["Data Management"])
    
    from app.routes.api.admin import router as admin_router
    from app.routes.auth.password_change import password_router

    app.include_router(admin_router, prefix="/admin", tags=["Admin CRUD"])
    app.include_router(password_router, prefix="/auth", tags=["Password Management"])

except Exception as e:
    print(f"[ERROR][APP] - Ошибка подключения роутов: {e}")
    import traceback
    traceback.print_exc()

@app.on_event("startup")
async def startup_event():
    
    try:
        from app.core.dynamodb.connector import get_db_connector
        connector = get_db_connector()
        
        if connector:
            
            system_info = connector.get_system_info()
            print(f"[INFO][APP] - Статус БД: {system_info.get('status')}")
            print(f"[INFO][APP] - Таблиц: {system_info.get('total_tables')}")
        else:
            print("[ERROR][APP] - Не удалось инициализировать базу данных")
            
    except Exception as e:
        print(f"[ERROR][APP] - Ошибка инициализации: {e}")



if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )