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
    Realiza o scraping das vagas da Samsung usando Playwright + BeautifulSoup.
    - Carrega a página com Playwright para aguardar renderização JS
    - Extrai informações com BeautifulSoup
    - Filtra vagas de Campinas, Brazil
    """
    
    url = EMPRESA_URLS.get("Samsung")
    if not url:
        print("❌ URL da Samsung não encontrada nas configurações.")
        return []

    vagas_para_salvar = []

    print(f"Iniciando scraper para a Samsung em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        html_content = ""
        
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

            # Scroll suave para garantir que todas as vagas renderizem
            print("Rolando a página para carregar todas as vagas...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # Extrai o HTML completo
            html_content = page.content()
            
        except Exception as e:
            print(f"❌ Erro ao carregar a página: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")

    if not html_content:
        return []

    print("\nIniciando parse com BeautifulSoup...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Encontra todas as vagas: <li class="css-1q2dra3">
    vagas_items = soup.find_all('li', class_='css-1q2dra3')
    
    if not vagas_items:
        print("⚠️ Nenhuma vaga encontrada na página.")
        return []
    
    print(f"Encontradas {len(vagas_items)} vagas na página.")
    
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
                url_vaga = f"https://sec.wd3.myworkdayjobs.com{url_relativa}"
            else:
                url_vaga = url_relativa
            
            # Localização
            location_div = item.find('div', {'data-automation-id': 'locations'})
            localizacao = ""
            if location_div:
                location_dd = location_div.find('dd', class_='css-129m7dg')
                if location_dd:
                    localizacao = location_dd.get_text(strip=True)
            
            # Tipo de trabalho (Remote Type)
            remote_div = item.find('div', {'data-automation-id': 'remoteType'})
            modelo_trabalho = "Presencial"
            if remote_div:
                remote_dd = remote_div.find('dd', class_='css-129m7dg')
                if remote_dd:
                    tipo_remote = remote_dd.get_text(strip=True)
                    if 'Remote' in tipo_remote:
                        modelo_trabalho = "Remoto"
                    elif 'Hybrid' in tipo_remote:
                        modelo_trabalho = "Híbrido"
                    elif 'On-site' in tipo_remote:
                        modelo_trabalho = "Presencial"
            
            # Filtro de localização - só Campinas
            if not localizacao:
                continue
            
            local_lower = localizacao.lower()
            if 'campinas' not in local_lower:
                continue
            
            # Monta o dicionário da vaga
            dados_vaga = {
                "empresa": "Samsung",
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
    
    print(f"\n✅ Total de vagas coletadas da Samsung: {len(vagas_para_salvar)}")
    return vagas_para_salvar


# Bloco para execução direta (útil para testes)
if __name__ == "__main__":
    print("=== TESTE DO SCRAPER SAMSUNG ===\n")
    vagas = raspar()
    
    print("\n=== RESULTADO ===")
    print(f"Total de vagas encontradas: {len(vagas)}")
    
    if vagas:
        print("\nPrimeiras vagas:")
        for i, vaga in enumerate(vagas[:5], 1):
            print(f"\n{i}. {vaga['titulo']}")
            print(f"   Localização: {vaga['localizacao']}")
            print(f"   Modelo: {vaga['modelo_trabalho']}")
            print(f"   URL: {vaga['url_vaga']}")
