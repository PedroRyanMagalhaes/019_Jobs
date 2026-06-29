"""
TEMPLATE para testes de scrapers com SQLite isolado
Copie este arquivo e adapte para cada scraper
"""
import sys
from pathlib import Path
import sqlite3
import os

root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers import SeuScraper  # ADAPTE AQUI
from config.settings import SCRAPER_CONFIG

TEST_DB_FILE = "src/database/teste.db"

def criar_banco_teste():
    """Cria banco de teste isolado com SQLite"""
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
    """Testa o scraper"""
    
    print(f"--- TESTANDO SCRAPER ---")
    print(f"Usando banco de teste isolado: {TEST_DB_FILE}\n")
    
    # Cria banco teste
    criar_banco_teste()
    
    # Configura headless
    SCRAPER_CONFIG["headless"] = False
    
    # Executa o scraper
    vagas_coletadas = SeuScraper.raspar()  # ADAPTE AQUI

    # Assertions
    assert vagas_coletadas, "❌ Nenhuma vaga encontrada."
    assert len(vagas_coletadas) > 0, "Lista de vagas está vazia"
    
    print(f"✅ SUCESSO! {len(vagas_coletadas)} vagas encontradas.\n")
    print(f"Primeiras 3 vagas:")
    for i, vaga in enumerate(vagas_coletadas[:3], 1):
        print(f"  {i}. {vaga['titulo']} ({vaga.get('localizacao', 'N/A')})")
    
    # Salva no banco teste isolado
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
    
    # Limpa após teste (opcional - comente se quiser manter para inspecionar)
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
        print(f"✓ Banco de teste removido.")


if __name__ == "__main__":
    test_scraper()
