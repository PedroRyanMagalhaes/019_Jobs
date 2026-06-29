from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

_client: Client | None = None


def get_supabase() -> Client:
    """Retorna o cliente Supabase (singleton). Usa service_role para acesso backend."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY precisam estar definidos no .env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client
