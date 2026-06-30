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

from src.newsletter.buscar_vagas import buscar_vagas_recentes, contar_vagas_filtradas, contar_vagas_por_origem
from src.newsletter.gerenciar_assinantes import buscar_assinantes_ativos, buscar_assinante_dev
from config.settings import GITHUB_PAGES_URL

# Carregar variáveis de ambiente
load_dotenv()

def renderizar_newsletter(vagas, total_vagas_ativas, pagina_url, token_usuario=''):
    """Renderiza template HTML com Jinja2"""
    template_dir = os.path.join('src', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('newsletter_base.html')

    return template.render(
        data_hoje=datetime.now().strftime('%d/%m/%Y'),
        total_vagas=len(vagas),
        vagas=vagas,
        total_vagas_ativas=total_vagas_ativas,
        pagina_url=pagina_url,
        token=token_usuario
    )

def enviar_emails(teste=False, dev=False):
    """
    Envia newsletter para os assinantes.

    Args:
        teste: Se True, envia apenas para o primeiro assinante da lista
        dev:   Se True, envia apenas para o assinante id=1 (ambiente de desenvolvimento)
    """
    # Configurar Resend
    resend.api_key = os.getenv('RESEND_API_KEY')
    email_from = os.getenv('EMAIL_FROM', 'noreply@zerodezenovejobs.com.br')
    
    if not resend.api_key:
        print("❌ RESEND_API_KEY não encontrada no .env")
        return
    
    if not email_from:
        print("❌ EMAIL_FROM não encontrada no .env")
        return
    
    # Buscar assinantes e vagas
    if dev:
        assinantes = buscar_assinante_dev()
        print("🛠️  MODO DEV — enviando apenas para assinante id=1")
    else:
        assinantes = buscar_assinantes_ativos()
    vagas = buscar_vagas_recentes(dias=1)
    total_vagas_ativas = contar_vagas_filtradas()
    pagina_url = GITHUB_PAGES_URL

    if not assinantes:
        print("⚠️ Nenhum assinante ativo encontrado")
        return

    print(f"\n📧 Preparando envio para {len(assinantes)} assinantes...")
    print(f"🚀 {len(vagas)} vagas novas hoje")
    print(f"📋 {total_vagas_ativas} vagas ativas no total")
    
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
        html = renderizar_newsletter(vagas, total_vagas_ativas, pagina_url, assinante['token'])
        
        try:
            params = {
                'from': f'019_JOBS <{email_from}>',
                'to': [assinante['email']],
                'subject': f"🎆 {len(vagas)} Novas Vagas • {datetime.now().strftime('%d/%m/%Y')}",
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
    parser.add_argument('--teste', action='store_true', help='Modo teste (envia apenas para o primeiro assinante)')
    parser.add_argument('--dev', action='store_true', help='Modo dev (envia apenas para assinante id=1)')
    args = parser.parse_args()

    enviar_emails(teste=args.teste, dev=args.dev)
