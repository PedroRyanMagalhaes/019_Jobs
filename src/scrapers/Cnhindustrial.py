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

def raspar(headless=None):
    """
    Realiza o scraping das vagas da CNH Industrial usando Playwright + BeautifulSoup.
    - URL já filtrada para Brasil
    - Carrega a página com Playwright para aguardar renderização JS
    - Extrai informações com BeautifulSoup
    - Filtra vagas apenas de Sorocaba
    
    Args:
        headless: Se None, usa SCRAPER_CONFIG. Se True/False, força o modo.
    """
    
    url = EMPRESA_URLS.get("Cnhindustrial")
    if not url:
        print("❌ URL da CNH Industrial não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://join.cnh.com"

    print(f"Iniciando scraper para a CNH Industrial em {url}")

    # Define headless: usa parâmetro se fornecido, senão usa config
    use_headless = SCRAPER_CONFIG.get("headless", True) if headless is None else headless

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=use_headless)
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="pt-BR"  # Força o idioma Português
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- ETAPA 1: ACEITAR COOKIES ---
            print("Procurando por banner de cookies...")
            try:
                cookie_button = page.locator("#cookie-accept")
                cookie_button.wait_for(state="visible", timeout=10000)
                cookie_button.click()
                print("✅ Cookies aceitos.")
                time.sleep(2)
            except:
                print("⚠️ Banner de cookies não encontrado (já pode ter sido aceito).")

            # --- ETAPA 2: CLICAR NO FILTRO BRASIL ---
            print("Aplicando filtro de Brasil...")
            try:
                # Aguarda o checkbox aparecer
                brazil_checkbox = page.locator('ui5-checkbox-xweb-rmk-jobs-search[data-testid="filter_jobLocationCountry_6"]')
                brazil_checkbox.wait_for(state="visible", timeout=10000)
                
                # Verifica se já está marcado
                is_checked = brazil_checkbox.get_attribute("aria-checked")
                if is_checked == "false":
                    brazil_checkbox.click()
                    print("✅ Filtro Brasil aplicado.")
                    time.sleep(3)  # Aguarda carregar as vagas
                else:
                    print("✅ Filtro Brasil já estava aplicado.")
            except Exception as e:
                print(f"⚠️ Erro ao aplicar filtro Brasil: {e}")
                print("Continuando mesmo assim (URL pode já ter o filtro)...")

            # --- ETAPA 3: AGUARDAR LISTA DE VAGAS ---
            print("Aguardando lista de vagas carregar...")
            try:
                page.wait_for_selector('li[data-testid="jobCard"]', timeout=15000)
                print("✅ Lista de vagas encontrada.")
            except:
                print("⚠️ Lista de vagas não encontrada.")
                return []
            
            page_num = 1
            
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                # Scroll para carregar todas as vagas
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Extrai o HTML da página atual
                html_content = page.content()
                
                # Parse com BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Encontra os cartões de vagas
                vagas_items = soup.find_all('li', {'data-testid': 'jobCard'})
                
                print(f"Analisando {len(vagas_items)} vagas encontradas.")
                
                if len(vagas_items) == 0:
                    print("⚠️ Nenhuma vaga encontrada nesta página.")
                    break
                
                for item in vagas_items:
                    try:
                        # Título e URL
                        link_tag = item.find('a', class_='jobCardTitle')
                        if not link_tag:
                            continue
                        
                        titulo = link_tag.get_text(strip=True)
                        url_relativa = link_tag.get('href', '')
                        
                        # Monta URL completa
                        if url_relativa.startswith('http'):
                            url_vaga = url_relativa
                        elif url_relativa.startswith('/'):
                            url_vaga = f"{base_url}{url_relativa}"
                        else:
                            url_vaga = f"{base_url}/{url_relativa}"
                        
                        # Localização
                        location_div = item.find('div', {'data-testid': 'jobCardLocation'})
                        if not location_div:
                            continue
                        
                        localizacao = location_div.get_text(strip=True)
                        
                        # Filtro de localização - só Sorocaba
                        local_lower = localizacao.lower()
                        if 'sorocaba' not in local_lower:
                            continue
                        
                        # Modelo de trabalho - busca nos footers
                        modelo_trabalho = "Não informado"
                        footer_values = item.find_all('span', class_='JobsList_jobCardFooterValue__Lc--j')
                        
                        for value in footer_values:
                            texto = value.get_text(strip=True)
                            if texto in ['Híbrido', 'Hybrid']:
                                modelo_trabalho = "Híbrido"
                                break
                            elif texto in ['Totalmente Presencial', 'On-site']:
                                modelo_trabalho = "Presencial"
                                break
                            elif texto in ['Remoto', 'Remote']:
                                modelo_trabalho = "Remoto"
                                break
                        
                        # Monta o dicionário da vaga
                        dados_vaga = {
                            "empresa": "CNH Industrial",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo_trabalho,
                            "url_vaga": url_vaga
                        }
                        
                        vagas_para_salvar.append(dados_vaga)
                        print(f"  [VAGA VÁLIDA] {dados_vaga['titulo']} ({dados_vaga['localizacao']}) - {modelo_trabalho}")
                        
                    except Exception as e:
                        print(f"⚠️ Erro ao processar vaga: {e}")
                        continue
                
                # Tenta avançar para a próxima página
                try:
                    # Verifica se existe botão de próxima página
                    next_button = page.locator('button[aria-label*="ext"]').or_(page.locator('button:has-text("Próximo")'))
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
    
    print(f"\n✅ Total de vagas coletadas da CNH Industrial: {len(vagas_para_salvar)}")
    return vagas_para_salvar


# Bloco para execução direta (útil para testes)
if __name__ == "__main__":
    print("=== TESTE DO SCRAPER CNH INDUSTRIAL ===\n")
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
