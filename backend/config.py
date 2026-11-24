import os
from typing import List

class Settings:
    PROJECT_NAME: str = "RevenueGuard"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Environment mode: development, testing, production
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    
    # Debug mode is strictly disabled in production
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes") if os.getenv("ENVIRONMENT", "").lower() != "production" else False
    
    # Interactive API Documentation: disabled in production by default unless explicitly enabled
    DOCS_ENABLED: bool = os.getenv("DOCS_ENABLED", "true" if os.getenv("ENVIRONMENT", "").lower() != "production" else "false").lower() in ("true", "1", "yes")

    # Database URL: default to sqlite for self-contained execution, override with postgresql://...
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./revenueguard.db")
    
    # Application Secret Key (must be overridden in production)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "revenueguard-insecure-dev-secret-key-change-in-prod")
    
    # Allowed CORS Origins
    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw_origins = os.getenv("ALLOWED_ORIGINS", "")
        if raw_origins:
            return [o.strip() for o in raw_origins.split(",") if o.strip()]
        
        # Development safe defaults
        if self.ENVIRONMENT == "production":
            return ["http://localhost", "https://localhost"]
        
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]

settings = Settings()

