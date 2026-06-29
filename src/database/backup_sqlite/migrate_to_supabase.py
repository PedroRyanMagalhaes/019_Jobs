"""
Script de migração: SQLite -> Supabase
- Faz backup dos arquivos .db para src/database/backup_sqlite/
- Migra todos os dados para o Supabase

Execute: python migrate_to_supabase.py
"""
import sqlite3
import os
import shutil
from datetime import datetime
from src.database.supabase_client import get_supabase

# Caminhos dos bancos SQLite
DB_VAGAS      = "src/database/vagas.db"
DB_REMOVIDAS  = "src/database/removidas.db"
DB_FILTRADAS  = "src/database/vagas_filtradas.db"
DB_USUARIOS   = "src/database/usuarios_newsletter.db"
BACKUP_DIR    = "src/database/backup_sqlite"


def fazer_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bancos = [DB_VAGAS, DB_REMOVIDAS, DB_FILTRADAS, DB_USUARIOS]
    for db in bancos:
        if os.path.exists(db):
            nome = os.path.basename(db).replace(".db", f"_{timestamp}.db")
            destino = os.path.join(BACKUP_DIR, nome)
            shutil.copy2(db, destino)
            print(f"✅ Backup: {db} -> {destino}")
        else:
            print(f"⚠️  Não encontrado (pulando): {db}")


def migrar_vagas(sb):
    if not os.path.exists(DB_VAGAS):
        print("⚠️  vagas.db não encontrado, pulando...")
        return
    conn = sqlite3.connect(DB_VAGAS)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM vagas").fetchall()
    conn.close()
    if not rows:
        print("ℹ️  Nenhuma vaga para migrar.")
        return
    dados = [dict(r) for r in rows]
    for d in dados:
        d.pop("id", None)  # deixar o Supabase gerar o id
    sb.table("vagas").upsert(dados, on_conflict="url_vaga").execute()
    print(f"✅ {len(dados)} vagas migradas.")


def migrar_removidas(sb):
    if not os.path.exists(DB_REMOVIDAS):
        print("⚠️  removidas.db não encontrado, pulando...")
        return
    conn = sqlite3.connect(DB_REMOVIDAS)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM vagas_removidas").fetchall()
    conn.close()
    if not rows:
        print("ℹ️  Nenhuma vaga removida para migrar.")
        return
    dados = [dict(r) for r in rows]
    for d in dados:
        d.pop("id", None)
    sb.table("vagas_removidas").insert(dados).execute()
    print(f"✅ {len(dados)} vagas removidas migradas.")


def migrar_filtradas(sb):
    if not os.path.exists(DB_FILTRADAS):
        print("⚠️  vagas_filtradas.db não encontrado, pulando...")
        return
    conn = sqlite3.connect(DB_FILTRADAS)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM vagas_filtradas").fetchall()
    conn.close()
    if not rows:
        print("ℹ️  Nenhuma vaga filtrada para migrar.")
        return
    dados = [dict(r) for r in rows]
    for d in dados:
        d.pop("id", None)
    sb.table("vagas_filtradas").upsert(dados, on_conflict="url_vaga").execute()
    print(f"✅ {len(dados)} vagas filtradas migradas.")


def migrar_usuarios(sb):
    if not os.path.exists(DB_USUARIOS):
        print("⚠️  usuarios_newsletter.db não encontrado, pulando...")
        return
    conn = sqlite3.connect(DB_USUARIOS)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM assinantes").fetchall()
    conn.close()
    if not rows:
        print("ℹ️  Nenhum assinante para migrar.")
        return
    dados = [dict(r) for r in rows]
    for d in dados:
        d.pop("id", None)
    sb.table("assinantes").upsert(dados, on_conflict="email").execute()
    print(f"✅ {len(dados)} assinantes migrados.")


if __name__ == "__main__":
    print("=" * 50)
    print("🔄 Iniciando migração SQLite -> Supabase")
    print("=" * 50)

    print("\n📦 Fazendo backup dos arquivos SQLite...")
    fazer_backup()

    sb = get_supabase()

    print("\n📤 Migrando dados...")
    migrar_vagas(sb)
    migrar_removidas(sb)
    migrar_filtradas(sb)
    migrar_usuarios(sb)

    print("\n✅ Migração concluída!")
