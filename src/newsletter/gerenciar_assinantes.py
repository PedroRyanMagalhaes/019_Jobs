"""
Funções para gerenciar assinantes da newsletter via Supabase
"""
import uuid
from src.database.supabase_client import get_supabase


def adicionar_assinante(email, nome='', ativo=True):
    """Adiciona um novo assinante"""
    sb = get_supabase()
    token = str(uuid.uuid4())
    res = sb.table("assinantes").select("id").eq("email", email).execute()
    if res.data:
        print(f"⚠️ {email} já está cadastrado")
        return False
    sb.table("assinantes").insert({
        "email": email,
        "nome": nome,
        "token_cancelamento": token,
        "ativo": ativo
    }).execute()
    status = "✅ ATIVO" if ativo else "❌ INATIVO"
    print(f"✅ {email} adicionado como {status}!")
    return True


def remover_assinante(email=None, token=None):
    """Desativa assinante por email ou token"""
    sb = get_supabase()
    if token:
        sb.table("assinantes").update({"ativo": False}).eq("token_cancelamento", token).execute()
    elif email:
        sb.table("assinantes").update({"ativo": False}).eq("email", email).execute()
    else:
        print("❌ Forneça email ou token")
        return False
    print("✅ Assinante removido com sucesso!")
    return True


def listar_assinantes(apenas_ativos=True):
    """Lista todos os assinantes"""
    sb = get_supabase()
    query = sb.table("assinantes").select("id, email, nome, data_inscricao, ativo")
    if apenas_ativos:
        query = query.eq("ativo", True)
    res = query.execute()
    assinantes = res.data
    print(f"\n📧 Total de assinantes: {len(assinantes)}\n")
    for a in assinantes:
        status = "✅ Ativo" if a["ativo"] else "❌ Inativo"
        print(f"ID: {a['id']} | Email: {a['email']} | Nome: {a['nome']} | Data: {a['data_inscricao']} | {status}")
    return assinantes


def buscar_assinantes_ativos():
    """Retorna lista de assinantes ativos para envio"""
    sb = get_supabase()
    res = sb.table("assinantes").select("email, nome, token_cancelamento").eq("ativo", True).execute()
    return [{
        'email': a['email'],
        'nome': a['nome'],
        'token': a['token_cancelamento']
    } for a in res.data]


if __name__ == '__main__':
    print("=== Gerenciamento de Assinantes ===")
    adicionar_assinante('seu_email@exemplo.com', 'Seu Nome')
    listar_assinantes()
