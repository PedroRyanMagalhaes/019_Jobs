# Ajusta o path quando executado diretamente
if __name__ == "__main__":
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))

import time
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG

def raspar():
    """
    Realiza o scraping das vagas da Toyota usando Playwright + BeautifulSoup.
    - URL já filtrada para Sorocaba e Indaiatuba
    - Todas as vagas são marcadas como Híbrido
    - Carrega a página com Playwright para aguardar renderização JS
    - Extrai informações com BeautifulSoup
    """
    
    url = EMPRESA_URLS.get("Toyota")
    if not url:
        print("❌ URL da Toyota não encontrada nas configurações.")
        return []

    vagas_para_salvar = []

    print(f"Iniciando scraper para a Toyota em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # Espera a lista de vagas aparecer
            try:
                page.wait_for_selector('li.css-1q2dra3', timeout=15000)
                print("✅ Lista de vagas encontrada.")
            except:
                print("⚠️ Lista de vagas não encontrada.")
                return []

            page_num = 1
            
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                # Scroll suave para garantir que todas as vagas renderizem
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Extrai o HTML da página atual
                html_content = page.content()
                
                # Parse com BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                vagas_items = soup.find_all('li', class_='css-1q2dra3')
                
                print(f"Analisando {len(vagas_items)} vagas encontradas.")
                
                for item in vagas_items:
                    try:
                        # Título e URL
                        link_tag = item.find('a', {'data-automation-id': 'jobTitle'})
                        if not link_tag:
                            continue
                        
                        titulo = link_tag.get_text(strip=True)
                        url_relativa = link_tag.get('href', '')
                        
                        # Monta URL completa
                        if url_relativa.startswith('/'):
                            url_vaga = f"https://toyota.wd503.myworkdayjobs.com{url_relativa}"
                        else:
                            url_vaga = url_relativa
                        
                        # Localização
                        location_div = item.find('div', {'data-automation-id': 'locations'})
                        localizacao = "Sorocaba/Indaiatuba - SP"
                        if location_div:
                            location_dd = location_div.find('dd', class_='css-129m7dg')
                            if location_dd:
                                localizacao = location_dd.get_text(strip=True)
                        
                        # Todas as vagas são Híbrido (conforme solicitado)
                        modelo_trabalho = "Híbrido"
                        
                        # Monta o dicionário da vaga
                        dados_vaga = {
                            "empresa": "Toyota",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo_trabalho,
                            "url_vaga": url_vaga
                        }
                        
                        vagas_para_salvar.append(dados_vaga)
                        print(f"  [VAGA VÁLIDA] {dados_vaga['titulo']} ({dados_vaga['localizacao']})")
                        
                    except Exception as e:
                        print(f"⚠️ Erro ao processar vaga: {e}")
                        continue
                
                # Verifica se existe botão "next" e se está habilitado
                try:
                    next_button = page.locator('button[aria-label="next"]')
                    if next_button.count() > 0 and next_button.is_enabled():
                        print("Avançando para a próxima página...")
                        next_button.click()
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                        page_num += 1
                    else:
                        print("Não há mais páginas.")
                        break
                except Exception:
                    print("Não há mais páginas.")
                    break
            
        except Exception as e:
            print(f"❌ Erro ao carregar a página: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")
    
    print(f"\n✅ Total de vagas coletadas da Toyota: {len(vagas_para_salvar)}")
    return vagas_para_salvar



