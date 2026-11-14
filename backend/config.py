import os

class Settings:
    PROJECT_NAME: str = "RevenueGuard"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database URL: default to sqlite for self-contained execution, override with postgresql://user:password@localhost:5432/revenueguard
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./revenueguard.db")
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()
