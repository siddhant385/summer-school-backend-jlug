from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List

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

    # Content Moderation Configuration
    ENABLE_CONTENT_MODERATION: bool = True
    MAX_REVIEW_LENGTH: int = 1000
    ENABLE_SPAM_DETECTION: bool = True
    
    # Custom bad words list (comma-separated in env, list in code)
    # This should be empty by default and populated by users as needed
    CUSTOM_BAD_WORDS: str = ""
    
    @property
    def bad_words_list(self) -> List[str]:
        """Convert comma-separated string to list of bad words"""
        if not self.CUSTOM_BAD_WORDS or not self.CUSTOM_BAD_WORDS.strip():
            return []
        return [word.strip().lower() for word in self.CUSTOM_BAD_WORDS.split(",") if word.strip()]

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding='utf-8'
    )

settings = Settings()

# Ab aise use karenge:
# print(settings.APP_NAME)
# print(settings.SUPABASE_URL)
# print(settings.SECRET_KEY.get_secret_value())  # Actual value ke liye