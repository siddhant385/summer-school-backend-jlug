# app/core/db.py

from supabase import create_client, Client
# Import the central settings object
from .config import settings
# Import your logger setup function
from .logger import setup_logger

# Set up the logger for this module
log = setup_logger(__name__)

supabase_client: Client | None = None
supabase_admin_client: Client | None = None

try:
    # Use the validated settings to create the standard client
    supabase_client = create_client(
        str(settings.SUPABASE_URL), # Convert AnyHttpUrl to string
        settings.SUPABASE_ANON_KEY
    )
    log.debug("✅ Supabase standard client (anon) initialized.")

    # Use the secure settings to create the admin client
    supabase_admin_client = create_client(
        str(settings.SUPABASE_URL),
        settings.SUPABASE_SERVICE_KEY.get_secret_value() # Get the real secret value
    )
    log.debug("✅ Supabase admin client (service_role) initialized.")

except Exception as e:
    # Now the logger is defined and can be used here
    log.error(f"❌ Error initializing Supabase clients: {e}", exc_info=True)

# --- FastAPI Dependencies ---

def get_db() -> Client:
    """Dependency to get the standard (anon) Supabase client."""
    if supabase_client is None:
        raise RuntimeError("Supabase client is not available.")
    return supabase_client

def get_db_admin() -> Client:
    """Dependency to get the admin (service_role) Supabase client."""
    if supabase_admin_client is None:
        raise RuntimeError("Supabase admin client is not available.")
    return supabase_admin_client