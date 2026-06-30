"""
Busca vagas tech do Supabase (tabela vagas_filtradas)
"""
from datetime import date
from src.database.supabase_client import get_supabase


def buscar_vagas_recentes(dias=1):
    """
    Busca vagas tech coletadas APENAS HOJE.
    O parâmetro dias é mantido por compatibilidade.
    """
    sb = get_supabase()
    data_hoje = date.today().isoformat()
    res = sb.table("vagas_filtradas").select(
        "titulo, empresa, localizacao, url_vaga, data_coleta, classificacao_funil"
    ).eq("data_coleta", data_hoje).order("data_coleta", desc=True).execute()

    return [{
        'titulo': v['titulo'],
        'empresa': v['empresa'],
        'localizacao': v['localizacao'] or 'Não especificado',
        'link': v['url_vaga'],
        'data': v['data_coleta'],
        'origem': v['classificacao_funil']
    } for v in res.data]


def buscar_vagas_ativas():
    """
    Busca todas as vagas tech ativas (anteriores a hoje).
    """
    sb = get_supabase()
    data_hoje = date.today().isoformat()
    res = sb.table("vagas_filtradas").select(
        "titulo, empresa, localizacao, url_vaga, data_coleta, classificacao_funil"
    ).lt("data_coleta", data_hoje).order("data_coleta", desc=True).execute()

    return [{
        'titulo': v['titulo'],
        'empresa': v['empresa'],
        'localizacao': v['localizacao'] or 'Não especificado',
        'link': v['url_vaga'],
        'data': v['data_coleta'],
        'origem': v['classificacao_funil']
    } for v in res.data]


def contar_vagas_filtradas():
    """Conta o total de vagas ativas na tabela vagas_filtradas."""
    sb = get_supabase()
    res = sb.table("vagas_filtradas").select("id", count="exact").execute()
    return res.count or 0


def contar_vagas_por_origem():
    """Conta quantas vagas vieram do filtro vs IA hoje"""
    sb = get_supabase()
    data_hoje = date.today().isoformat()
    res = sb.table("vagas_filtradas").select("classificacao_funil").eq("data_coleta", data_hoje).execute()
    stats = {}
    for v in res.data:
        k = v['classificacao_funil']
        stats[k] = stats.get(k, 0) + 1
    return stats


if __name__ == '__main__':
    print("🔍 Buscando vagas recentes...\n")
    vagas = buscar_vagas_recentes()
    print(f"Total: {len(vagas)} vagas")
    print(f"📊 {len(vagas)} vagas encontradas\n")
    
    for i, vaga in enumerate(vagas[:5], 1):
        print(f"{i}. {vaga['titulo']}")
        print(f"   {vaga['empresa']} | {vaga['localizacao']}")
        print(f"   Origem: {vaga['origem']}\n")
    
    # Estatísticas
    stats = contar_vagas_por_origem()
    print("\n📈 Estatísticas de hoje:")
    for origem, count in stats.items():
        print(f"   {origem}: {count} vagas")
