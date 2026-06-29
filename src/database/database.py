from datetime import date, datetime
from src.database.supabase_client import get_supabase


def inicializar_banco():
    """Verifica conexao com o Supabase (tabelas ja criadas via supabase_schema.sql)."""
    sb = get_supabase()
    sb.table("vagas").select("id").limit(1).execute()
    print("Conexao com Supabase verificada.")


def salvar_vaga(dados_vaga: dict) -> bool:
    """
    Insere vaga nova ou atualiza ultima_atualizacao se ja existir.
    Retorna True se era nova, False se ja existia.
    """
    sb = get_supabase()
    dados_vaga = dict(dados_vaga)
    dados_vaga["data_coleta"] = date.today().isoformat()
    dados_vaga["ultima_atualizacao"] = datetime.now().isoformat()
    dados_vaga.pop("id", None)

    res = sb.table("vagas").select("id").eq("url_vaga", dados_vaga["url_vaga"]).execute()
    if res.data:
        sb.table("vagas").update({"ultima_atualizacao": dados_vaga["ultima_atualizacao"]}).eq(
            "url_vaga", dados_vaga["url_vaga"]
        ).execute()
        return False

    sb.table("vagas").insert(dados_vaga).execute()
    print(f"Vaga nova salva: '{dados_vaga['titulo']}' ({dados_vaga.get('modelo_trabalho', 'N/A')})")
    return True


def iniciar_ciclo_scraping():
    print("Iniciando novo ciclo de scraping...")


def finalizar_ciclo_scraping():
    """Move vagas nao atualizadas hoje para vagas_removidas e as apaga."""
    print("Finalizando ciclo de scraping e limpando vagas antigas...")
    sb = get_supabase()
    data_hoje = datetime.now().date().isoformat()

    res = sb.table("vagas").select("*").lt("ultima_atualizacao", data_hoje).execute()
    vagas_antigas = res.data

    if not vagas_antigas:
        print("Nenhuma vaga antiga encontrada")
        return

    print(f"{len(vagas_antigas)} vagas para mover para removidas...")

    agora = datetime.now().isoformat()
    removidas = []
    for v in vagas_antigas:
        removidas.append({
            "empresa": v["empresa"],
            "titulo": v["titulo"],
            "localizacao": v.get("localizacao"),
            "modelo_trabalho": v.get("modelo_trabalho"),
            "url_vaga": v["url_vaga"],
            "classificacao_ia": v.get("classificacao_ia"),
            "data_coleta": v["data_coleta"],
            "data_remocao": agora,
            "motivo_remocao": "Nao encontrada no ultimo scraping",
        })

    sb.table("vagas_removidas").insert(removidas).execute()

    urls = [v["url_vaga"] for v in vagas_antigas]
    for url in urls:
        sb.table("vagas").delete().eq("url_vaga", url).execute()
        sb.table("vagas_filtradas").delete().eq("url_vaga", url).execute()

    print(f"{len(vagas_antigas)} vagas movidas para vagas_removidas")


def contar_vagas() -> int:
    sb = get_supabase()
    res = sb.table("vagas").select("id", count="exact").execute()
    return res.count or 0


def contar_vagas_removidas() -> int:
    sb = get_supabase()
    res = sb.table("vagas_removidas").select("id", count="exact").execute()
    return res.count or 0
