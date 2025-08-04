from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    # Application configuration
    APP_NAME: str = "Summer School Backend"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Supabase configuration
    SUPABASE_URL: AnyHttpUrl
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: SecretStr
    SUPABASE_PROJECT_ID: str
    
    # Security configuration
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Logging Config
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = Path("app.log") # Default log file name


    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding='utf-8'
    )

settings = Settings()

# Ab aise use karenge:
# print(settings.APP_NAME)
# print(settings.SUPABASE_URL)
# print(settings.SECRET_KEY.get_secret_value())  # Actual value ke liye