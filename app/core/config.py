# config.py for Supabase configuration
import os

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_PROJECT_ID: str = os.getenv("SUPABASE_PROJECT_ID", "")

settings = Settings()
