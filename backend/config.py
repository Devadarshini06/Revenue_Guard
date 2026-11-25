import os
from typing import List, Dict, Optional

class Settings:
    PROJECT_NAME: str = "RevenueGuard"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    def __init__(self, env_dict: Optional[Dict[str, str]] = None):
        self._env = env_dict if env_dict is not None else os.environ

    @property
    def ENVIRONMENT(self) -> str:
        return self._env.get("ENVIRONMENT", "development").lower()
    
    @property
    def DEBUG(self) -> bool:
        # Debug mode is strictly disabled in production
        if self.ENVIRONMENT == "production":
            return False
        return self._env.get("DEBUG", "false").lower() in ("true", "1", "yes")
    
    @property
    def DOCS_ENABLED(self) -> bool:
        val = self._env.get("DOCS_ENABLED")
        if val is not None:
            return val.lower() in ("true", "1", "yes")
        # In production docs are disabled by default
        return self.ENVIRONMENT != "production"

    @property
    def DATABASE_URL(self) -> str:
        return self._env.get("DATABASE_URL", "sqlite:///./revenueguard.db")
    
    @property
    def SECRET_KEY(self) -> str:
        return self._env.get("SECRET_KEY", "revenueguard-insecure-dev-secret-key-change-in-prod")
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw_origins = self._env.get("ALLOWED_ORIGINS", "")
        if raw_origins:
            origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
            if self.ENVIRONMENT == "production":
                # Strict production validation: Wildcard '*' must fail clearly at startup
                if "*" in origins:
                    raise ValueError(
                        "Insecure production configuration: Wildcard '*' in ALLOWED_ORIGINS is strictly prohibited in production mode. "
                        "Specify explicit trusted origins (e.g. 'https://analytics.revenueguard.com')."
                    )
                if not origins:
                    raise ValueError(
                        "Insecure production configuration: ALLOWED_ORIGINS contains no valid origins."
                    )
            return origins
        
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

    def validate_production_configuration(self) -> List[str]:
        """
        Validates required production environment settings.
        Returns a list of configuration violations or missing items.
        """
        issues = []
        if self.ENVIRONMENT == "production":
            secret = self._env.get("SECRET_KEY", "")
            if not secret or secret == "revenueguard-insecure-dev-secret-key-change-in-prod" or len(secret) < 32:
                issues.append("SECRET_KEY must be set to a cryptographically strong value (at least 32 characters) in production.")
            
            raw_origins = self._env.get("ALLOWED_ORIGINS", "")
            if not raw_origins:
                issues.append("ALLOWED_ORIGINS must be explicitly configured in production.")
            elif "*" in [o.strip() for o in raw_origins.split(",")]:
                issues.append("Wildcard '*' in ALLOWED_ORIGINS is prohibited in production.")
        return issues

settings = Settings()
