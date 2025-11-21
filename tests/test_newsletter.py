"""
Testes para o sistema de newsletter
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.newsletter.buscar_vagas import buscar_vagas_recentes, contar_vagas_por_origem
from src.newsletter.gerenciar_assinantes import buscar_assinantes_ativos
from jinja2 import Environment, FileSystemLoader

def test_buscar_vagas():
    """Testa busca de vagas"""
    print("\n🔍 Testando busca de vagas...")
    vagas = buscar_vagas_recentes(dias=7)
    
    print(f"✅ {len(vagas)} vagas encontradas nos últimos 7 dias")
    
    if vagas:
        print("\n📋 Primeiras 3 vagas:")
        for i, vaga in enumerate(vagas[:3], 1):
            print(f"\n{i}. {vaga['titulo']}")
            print(f"   Empresa: {vaga['empresa']}")
            print(f"   Local: {vaga['localizacao']}")
            print(f"   Origem: {vaga['origem']}")
    
    return len(vagas) > 0

def test_estatisticas():
    """Testa contagem por origem"""
    print("\n📊 Testando estatísticas...")
    stats = contar_vagas_por_origem()
    
    if stats:
        print("✅ Estatísticas de hoje:")
        for origem, count in stats.items():
            print(f"   {origem}: {count} vagas")
    else:
        print("⚠️ Nenhuma vaga encontrada hoje")
    
    return True

def test_assinantes():
    """Testa busca de assinantes"""
    print("\n👥 Testando assinantes...")
    assinantes = buscar_assinantes_ativos()
    
    print(f"✅ {len(assinantes)} assinantes ativos")
    
    if assinantes:
        print("\n📧 Primeiro assinante:")
        print(f"   Email: {assinantes[0]['email']}")
        print(f"   Nome: {assinantes[0]['nome']}")
    
    return True

def test_template():
    """Testa renderização do template"""
    print("\n🎨 Testando template...")
    
    try:
        template_dir = os.path.join('src', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('newsletter_base.html')
        
        # Dados de teste
        vagas_teste = [{
            'titulo': 'Desenvolvedor Python Senior',
            'empresa': 'Tech Company',
            'localizacao': 'São Paulo, SP',
            'link': 'https://exemplo.com',
            'origem': 'tech funil'
        }]
        
        html = template.render(
            data_hoje='21/11/2025',
            total_vagas=1,
            vagas=vagas_teste,
            token='test-token-123'
        )
        
        print(f"✅ Template renderizado com sucesso! ({len(html)} caracteres)")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao renderizar template: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 TESTES DO SISTEMA DE NEWSLETTER")
    print("="*60)
    
    tests = [
        test_buscar_vagas,
        test_estatisticas,
        test_assinantes,
        test_template
    ]
    
    resultados = []
    for test in tests:
        try:
            resultado = test()
            resultados.append(resultado)
        except Exception as e:
            print(f"❌ Erro: {e}")
            resultados.append(False)
    
    print("\n" + "="*60)
    print(f"📊 RESULTADO: {sum(resultados)}/{len(tests)} testes passaram")
    print("="*60 + "\n")
