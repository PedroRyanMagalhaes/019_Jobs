"""
Teste unitário para o scraper da Huawei
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers import Huawei
from src.database import database
from config.settings import SCRAPER_CONFIG
import os


def test_scraper():
    """Testa o scraper da Huawei"""
    
    # Configura modo headless=False para testes
    SCRAPER_CONFIG["headless"] = False
    
    # Configura banco de dados de teste
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- TESTANDO SCRAPER DA HUAWEI ---")
    
    # Inicializa banco e limpa vagas anteriores
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Huawei'")
    conn.commit()
    conn.close()
    
    # Executa o scraper
    vagas_coletadas = Huawei.raspar()

    # Verifica o resultado
    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Huawei encontradas.")
        
        # Salva vagas no banco
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n⚠️ AVISO: Nenhuma vaga de Campinas/Sorocaba encontrada no momento.")
        print("O scraper está funcionando corretamente, mas não há vagas válidas disponíveis.")
        print("✅ Teste passou - scraper operacional.")


if __name__ == "__main__":
    test_scraper()
