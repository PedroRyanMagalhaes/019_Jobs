"""
Teste unitário para o scraper da ELDORADO
"""
import sys
from pathlib import Path
import sqlite3
import os

root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers import Eldorado

TEST_DB_FILE = "src/database/teste.db"

def criar_banco_teste():
    os.makedirs(os.path.dirname(TEST_DB_FILE), exist_ok=True)
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vagas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa TEXT NOT NULL,
        titulo TEXT NOT NULL,
        localizacao TEXT,
        modelo_trabalho TEXT,
        url_vaga TEXT NOT NULL UNIQUE,
        classificacao_ia TEXT,
        data_coleta TEXT NOT NULL,
        ultima_atualizacao TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def test_scraper():
    print(f"--- TESTANDO SCRAPER ELDORADO ---")
    print(f"Usando banco de teste isolado: {TEST_DB_FILE}\n")
    
    criar_banco_teste()
    vagas_coletadas = Eldorado.raspar()

    assert vagas_coletadas, "❌ Nenhuma vaga encontrada."
    assert len(vagas_coletadas) > 0, "Lista de vagas está vazia"
    
    print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas encontradas.")
    print(f"Primeiras 3 vagas:")
    for i, vaga in enumerate(vagas_coletadas[:3], 1):
        print(f"  {i}. {vaga['titulo']} ({vaga.get('localizacao', 'N/A')})") 
    
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
    novas_vagas_salvas = 0
    for vaga in vagas_coletadas:
        try:
            cursor.execute("""
            INSERT INTO vagas (empresa, titulo, localizacao, modelo_trabalho, url_vaga, data_coleta, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, DATE('now'), DATETIME('now'))
            """, (vaga.get('empresa'), vaga.get('titulo'), vaga.get('localizacao'), 
                   vaga.get('modelo_trabalho'), vaga.get('url_vaga')))
            novas_vagas_salvas += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    
    print(f"\nResumo: {novas_vagas_salvas} vagas salvas em '{TEST_DB_FILE}'.")
    
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

if __name__ == "__main__":
    test_scraper()
