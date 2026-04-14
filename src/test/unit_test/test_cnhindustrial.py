import pytest
import sys
from pathlib import Path

# Ajustar o sys.path para permitir importação dos módulos
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers.Cnhindustrial import raspar

def test_cnhindustrial_scraper():
    """
    Testa o scraper da CNH Industrial.
    Verifica se:
    - Retorna uma lista
    - Vagas possuem as chaves corretas
    - Empresa está correta
    - Localização contém apenas Sorocaba
    """
    print("\n🚜 Testando scraper da CNH Industrial...")
    
    vagas = raspar(headless=False)
    
    # Verifica se retorna uma lista
    assert isinstance(vagas, list), "O scraper deve retornar uma lista"
    
    print(f"✅ Total de vagas encontradas: {len(vagas)}")
    
    # Se houver vagas, verifica a estrutura
    if len(vagas) > 0:
        vaga = vagas[0]
        
        # Verifica as chaves obrigatórias
        assert "empresa" in vaga, "Vaga deve ter a chave 'empresa'"
        assert "titulo" in vaga, "Vaga deve ter a chave 'titulo'"
        assert "localizacao" in vaga, "Vaga deve ter a chave 'localizacao'"
        assert "modelo_trabalho" in vaga, "Vaga deve ter a chave 'modelo_trabalho'"
        assert "url_vaga" in vaga, "Vaga deve ter a chave 'url_vaga'"
        
        # Verifica se a empresa está correta
        assert vaga["empresa"] == "CNH Industrial", f"Empresa deve ser 'CNH Industrial', mas é '{vaga['empresa']}'"
        
        # Exibe informações da primeira vaga
        print(f"\n📋 Primeira vaga encontrada:")
        print(f"   Título: {vaga['titulo']}")
        print(f"   Localização: {vaga['localizacao']}")
        print(f"   Modelo: {vaga['modelo_trabalho']}")
        print(f"   URL: {vaga['url_vaga'][:80]}...")
        
        # Verifica se todas as localizações são de Sorocaba
        for v in vagas:
            local_lower = v["localizacao"].lower()
            assert 'sorocaba' in local_lower, \
                f"Localização '{v['localizacao']}' não é de Sorocaba"
        
        print(f"\n✅ Todas as {len(vagas)} vagas são de Sorocaba!")
    else:
        print("⚠️ Nenhuma vaga encontrada, mas o scraper executou sem erros.")
    
    print("\n✅ Teste do scraper da CNH Industrial concluído com sucesso!")

if __name__ == "__main__":
    test_cnhindustrial_scraper()
