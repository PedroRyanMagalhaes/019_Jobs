# Ajusta o path quando executado diretamente
if __name__ == "__main__":
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))

import time
import random
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG

def raspar(headless=None):
    """
    Realiza o scraping das vagas da AB InBev usando Playwright + BeautifulSoup.
    - LinkedIn (URL já filtrada por Greater Campinas)
    - Extrai TODAS as vagas da região
    - Empresa e localização são extraídas exatamente como aparecem no LinkedIn
    - Detecta modelo de trabalho baseado no título
    
    ATENÇÃO: LinkedIn tem proteções anti-bot. Pode ser necessário:
    - Adicionar delays maiores
    - Simular comportamento humano
    - Em alguns casos, pode requerer autenticação
    
    Args:
        headless: Se True/False, sobrescreve o valor do settings. Se None, usa o valor do settings.
    """
    
    url = EMPRESA_URLS.get("Abinbev")
    if not url:
        print("❌ URL da AB InBev não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    
    # Usa o parâmetro headless se fornecido, caso contrário usa o valor do settings
    use_headless = headless if headless is not None else SCRAPER_CONFIG.get("headless", True)

    print(f"Iniciando scraper para a AB InBev em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=use_headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="pt-BR",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")
            
            # Aguarda um pouco para verificar se aparece o modal de login
            time.sleep(random.uniform(2, 3))
            
            # Tenta fechar o modal de sign-in caso apareça
            try:
                modal_dismiss = page.locator(".contextual-sign-in-modal__modal-dismiss")
                if modal_dismiss.is_visible(timeout=2000):
                    modal_dismiss.click()
                    print("✅ Modal de login fechado.")
                    time.sleep(1)
            except Exception:
                # Modal não apareceu, seguir normalmente
                pass
            
            # Aguarda o loader desaparecer (LinkedIn carrega as vagas dinamicamente)
            print("Aguardando carregamento das vagas...")
            try:
                page.wait_for_selector(".loader--show", state="hidden", timeout=15000)
                print("✅ Loading finalizado.")
            except Exception:
                print("⚠️ Loading não desapareceu, tentando continuar...")
            
            # Aguarda a lista de vagas carregar
            time.sleep(random.uniform(2, 3))
            
            print("Aguardando lista de vagas carregar...")
            page.wait_for_selector("ul.jobs-search__results-list", timeout=15000)
            print("✅ Lista de vagas encontrada.")
            
            # Scroll lento e gradual para carregar mais vagas (simula comportamento humano)
            print("Fazendo scroll gradual para carregar todas as vagas...")
            scroll_num = 1
            while True:
                # Scroll em pequenos incrementos (como uma pessoa)
                page.evaluate(f"window.scrollBy(0, {random.randint(300, 500)})")
                time.sleep(random.uniform(2, 3.5))  # Delay maior entre scrolls
                
                # Verifica se apareceu a mensagem de "visualizou todas as vagas"
                try:
                    viewed_all = page.locator(".see-more-jobs__viewed-all")
                    if viewed_all.is_visible(timeout=1000):
                        print(f"✅ Todas as vagas foram carregadas (após {scroll_num} scrolls).")
                        break
                except Exception:
                    pass
                
                print(f"   Scroll {scroll_num}...")
                scroll_num += 1
            
            # Aguarda um pouco mais para garantir que tudo carregou
            time.sleep(2)
            
            # Obtém o HTML da página
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Encontra a lista de vagas
            lista_vagas = soup.find('ul', class_='jobs-search__results-list')
            
            if not lista_vagas:
                print("⚠️ Nenhuma lista de vagas encontrada.")
                return vagas_para_salvar
            
            # Encontra todos os cards de vaga
            vagas_cards = lista_vagas.find_all('li')
            print(f"✅ {len(vagas_cards)} vagas encontradas na página.")
            
            for idx, card in enumerate(vagas_cards, 1):
                try:
                    # Extrai o card principal
                    base_card = card.find('div', class_='base-card')
                    if not base_card:
                        continue
                    
                    # Extrai título
                    titulo_elem = base_card.find('h3', class_='base-search-card__title')
                    if not titulo_elem:
                        continue
                    titulo = titulo_elem.get_text(strip=True)
                    
                    # Extrai empresa
                    empresa_elem = base_card.find('h4', class_='base-search-card__subtitle')
                    if not empresa_elem:
                        continue
                    empresa_link = empresa_elem.find('a', class_='hidden-nested-link')
                    if not empresa_link:
                        continue
                    empresa = empresa_link.get_text(strip=True)
                    
                    # Extrai localização
                    localizacao_elem = base_card.find('span', class_='job-search-card__location')
                    if not localizacao_elem:
                        continue
                    localizacao = localizacao_elem.get_text(strip=True)
                    
                    # Extrai URL da vaga
                    link_elem = base_card.find('a', class_='base-card__full-link')
                    if not link_elem or not link_elem.get('href'):
                        continue
                    url_vaga = link_elem.get('href')
                    
                    # Determina modelo de trabalho baseado no título e descrição
                    titulo_lower = titulo.lower()
                    modelo_trabalho = "Presencial"  # Padrão
                    
                    if any(palavra in titulo_lower for palavra in ['remoto', 'remote', 'home office']):
                        modelo_trabalho = "Remoto"
                    elif any(palavra in titulo_lower for palavra in ['híbrido', 'hibrido', 'hybrid']):
                        modelo_trabalho = "Híbrido"
                    
                    # Cria o dicionário com os dados da vaga
                    dados_vaga = {
                        "empresa": empresa,
                        "titulo": titulo,
                        "localizacao": localizacao,
                        "modelo_trabalho": modelo_trabalho,
                        "url_vaga": url_vaga,
                    }
                    
                    vagas_para_salvar.append(dados_vaga)
                    print(f"  {idx}. {titulo} ({empresa}) - {localizacao}")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar vaga {idx}: {e}")
                    continue
            
        except TimeoutError:
            print(f"❌ Timeout ao tentar carregar a página: {url}")
        except Exception as e:
            print(f"❌ Erro inesperado no scraper da AB InBev: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")
    
    print(f"\n✅ Total de vagas coletadas da AB InBev: {len(vagas_para_salvar)}")
    return vagas_para_salvar



