import pytest
import sys
from pathlib import Path

# Ajustar o sys.path para permitir importação dos módulos
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers.Toyota import raspar

def test_toyota_scraper():
    """
    Testa o scraper da Toyota.
    Verifica se:
    - Retorna uma lista
    - Vagas possuem as chaves corretas
    - Empresa está correta
    - Modelo de trabalho é sempre Híbrido
    """
    print("\n🚗 Testando scraper da Toyota...")
    
    vagas = raspar()
    
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
        assert vaga["empresa"] == "Toyota", f"Empresa deve ser 'Toyota', mas é '{vaga['empresa']}'"
        
        # Verifica se o modelo de trabalho é sempre Híbrido
        assert vaga["modelo_trabalho"] == "Híbrido", f"Modelo deve ser 'Híbrido', mas é '{vaga['modelo_trabalho']}'"
        
        # Exibe informações da primeira vaga
        print(f"\n📋 Primeira vaga encontrada:")
        print(f"   Título: {vaga['titulo']}")
        print(f"   Localização: {vaga['localizacao']}")
        print(f"   Modelo: {vaga['modelo_trabalho']}")
        print(f"   URL: {vaga['url_vaga'][:80]}...")
        
        # Verifica todas as vagas para garantir que são Híbrido
        for v in vagas:
            assert v["modelo_trabalho"] == "Híbrido", f"Todas as vagas devem ser 'Híbrido'"
        
        print(f"\n✅ Todas as {len(vagas)} vagas são Híbrido!")
    else:
        print("⚠️ Nenhuma vaga encontrada, mas o scraper executou sem erros.")
    
    print("\n✅ Teste do scraper da Toyota concluído com sucesso!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
