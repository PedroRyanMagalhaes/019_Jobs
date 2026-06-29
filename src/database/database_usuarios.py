"""
Gerenciamento de assinantes da newsletter via Supabase.
"""
from src.database.supabase_client import get_supabase


def criar_banco_usuarios():
    """Verifica conexão com a tabela assinantes no Supabase."""
    sb = get_supabase()
    sb.table("assinantes").select("id").limit(1).execute()
    print("✅ Tabela assinantes verificada no Supabase.")


if __name__ == '__main__':
    criar_banco_usuarios()
