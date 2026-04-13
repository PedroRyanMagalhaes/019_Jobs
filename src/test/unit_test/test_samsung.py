"""
Teste unitário para o scraper da Samsung
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers import Samsung
from src.database import database
from config.settings import SCRAPER_CONFIG
import os


def test_scraper():
    """Testa o scraper da Samsung"""
    
    # Configura modo headless=False para testes
    SCRAPER_CONFIG["headless"] = False
    
    # Configura banco de dados de teste
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- TESTANDO SCRAPER DA SAMSUNG ---")
    
    # Inicializa banco e limpa vagas anteriores
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Samsung'")
    conn.commit()
    conn.close()
    
    # Executa o scraper
    vagas_coletadas = Samsung.raspar()

    # Assert: deve coletar pelo menos uma vaga
    assert vagas_coletadas, "❌ Nenhuma vaga da Samsung foi encontrada no teste."
    assert len(vagas_coletadas) > 0, "Lista de vagas está vazia"
    
    print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Samsung encontradas.")
    
    # Salva vagas no banco
    novas_vagas_salvas = 0
    for vaga in vagas_coletadas:
        if database.salvar_vaga(vaga):
            novas_vagas_salvas += 1
    
    print(f"✅ {novas_vagas_salvas} novas vagas da Samsung foram salvas no banco de teste.")
    
    # Verificações de qualidade
    print("\n--- VALIDANDO DADOS DAS VAGAS ---")
    for vaga in vagas_coletadas[:3]:  # Mostra apenas as 3 primeiras
        assert "empresa" in vaga, "Campo 'empresa' ausente"
        assert "titulo" in vaga, "Campo 'titulo' ausente"
        assert "localizacao" in vaga, "Campo 'localizacao' ausente"
        assert "url_vaga" in vaga, "Campo 'url_vaga' ausente"
        assert vaga["empresa"] == "Samsung", "Nome da empresa incorreto"
        
        print(f"\n✅ Vaga válida: {vaga['titulo']}")
        print(f"   Localização: {vaga['localizacao']}")
        print(f"   Modelo: {vaga['modelo_trabalho']}")
        print(f"   URL: {vaga['url_vaga'][:80]}...")
    
    print("\n=== TESTE COMPLETO ===")


if __name__ == "__main__":
    try:
        test_scraper()
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
