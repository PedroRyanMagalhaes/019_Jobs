"""
Script principal para enviar newsletter via Resend
"""
import sys
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import resend
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.newsletter.buscar_vagas import buscar_vagas_recentes, contar_vagas_por_origem
from src.newsletter.gerenciar_assinantes import buscar_assinantes_ativos

# Carregar variáveis de ambiente
load_dotenv()

def renderizar_newsletter(vagas, token_usuario=''):
    """Renderiza template HTML com Jinja2"""
    # Configurar Jinja2 para buscar templates
    template_dir = os.path.join('src', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('newsletter_base.html')
    
    return template.render(
        data_hoje=datetime.now().strftime('%d/%m/%Y'),
        total_vagas=len(vagas),
        vagas=vagas,
        token=token_usuario
    )

def enviar_emails(teste=False):
    """
    Envia newsletter para todos os assinantes
    
    Args:
        teste: Se True, envia apenas para você mesmo
    """
    # Configurar Resend
    resend.api_key = os.getenv('RESEND_API_KEY')
    
    if not resend.api_key:
        print("❌ RESEND_API_KEY não encontrada no .env")
        return
    
    # Buscar assinantes e vagas
    assinantes = buscar_assinantes_ativos()
    vagas = buscar_vagas_recentes(dias=1)
    
    if not assinantes:
        print("⚠️ Nenhum assinante ativo encontrado")
        return
    
    print(f"\n📧 Preparando envio para {len(assinantes)} assinantes...")
    print(f"🚀 {len(vagas)} vagas encontradas hoje")
    
    # Estatísticas
    stats = contar_vagas_por_origem()
    if stats:
        print("\n📈 Origem das vagas:")
        for origem, count in stats.items():
            print(f"   {origem}: {count}")
    
    print("\n" + "="*50)
    
    # Se for teste, enviar apenas para o primeiro assinante
    if teste:
        assinantes = assinantes[:1]
        print("🧪 MODO TESTE - Enviando apenas para o primeiro assinante")
    
    enviados = 0
    erros = 0
    
    for assinante in assinantes:
        html = renderizar_newsletter(vagas, assinante['token'])
        
        try:
            params = {
                'from': 'Vagas Tech <onboarding@resend.dev>',  # Email de teste do Resend
                'to': ['pedroryan.ra@outlook.com'],  # Só pode enviar pro seu email no plano gratuito
                'subject': f"🌆 {len(vagas)} Vagas Tech • {datetime.now().strftime('%d/%m/%Y')}",
                'html': html
            }
            
            resend.Emails.send(params)
            print(f"✅ Enviado para {assinante['email']}")
            enviados += 1
            
        except Exception as e:
            print(f"❌ Erro ao enviar para {assinante['email']}: {e}")
            erros += 1
    
    print("\n" + "="*50)
    print(f"\n📊 Resumo:")
    print(f"   ✅ Enviados: {enviados}")
    print(f"   ❌ Erros: {erros}")
    print(f"   📧 Total: {len(assinantes)}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enviar newsletter de vagas tech')
    parser.add_argument('--teste', action='store_true', help='Modo teste (envia apenas para você)')
    args = parser.parse_args()
    
    enviar_emails(teste=args.teste)
