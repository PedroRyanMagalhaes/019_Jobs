# Ajusta o path quando executado diretamente
if __name__ == "__main__":
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))

import time
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da IBM.
    - Filtra vagas de: Multiple Cities, NO City (Híbrido), e HORTOLANDIA (Hortolândia)
    - Suporta paginação
    """
    
    url = EMPRESA_URLS.get("Ibm")
    if not url:
        print("❌ URL da IBM não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://careers.ibm.com"

    print(f"Iniciando scraper para a IBM em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", False)
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

            # Espera um pouco para carregar conteúdo dinâmico
            page.wait_for_timeout(3000)

            # Aceitar cookies se aparecer
            try:
                print("Verificando banner de cookies...")
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("Aceitar"), button[id*="cookie"], button[class*="cookie"]').first
                if cookie_button.is_visible(timeout=3000):
                    cookie_button.click()
                    print("✅ Cookies aceitos.")
                    page.wait_for_timeout(1000)
            except:
                print("⚠️ Banner de cookies não encontrado ou já aceito.")

            page_num = 1
            
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                try:
                    # Aguarda carregar o container de vagas
                    page.wait_for_selector('div[data-autoid="dds--card-group"]', timeout=10000)
                except TimeoutError:
                    print("Nenhuma vaga encontrada na página (ou fim da lista).")
                    break
                
                # Localiza todos os cards de vagas
                vaga_cards = page.locator('div.bx--card-group__cards__col').all()
                print(f"Analisando {len(vaga_cards)} vagas na página.")

                vagas_encontradas_pagina = 0

                for card in vaga_cards:
                    try:
                        # Extrai o link
                        link_tag = card.locator('a.bx--card-group__card')
                        url_vaga_relativa = link_tag.get_attribute('href')
                        url_vaga = base_url + url_vaga_relativa if url_vaga_relativa.startswith('/') else url_vaga_relativa
                        
                        # Extrai o título
                        titulo_elem = card.locator('div.bx--card__heading')
                        titulo = titulo_elem.inner_text().strip()
                        
                        # Extrai a categoria
                        categoria_elem = card.locator('div.bx--card__eyebrow')
                        categoria = categoria_elem.inner_text().strip() if categoria_elem.count() > 0 else "Não informado"
                        
                        # Extrai o local (dentro de ibm--card__copy__inner)
                        local_elem = card.locator('div.ibm--card__copy__inner')
                        local_texto = local_elem.inner_text().strip().replace('\n', ' ')
                        
                        # Filtra por localização
                        local_lower = local_texto.lower()
                        
                        # Define localização e modelo baseado nos critérios
                        localizacao = None
                        modelo_trabalho = "Não informado"
                        
                        if "multiple cities" in local_lower:
                            localizacao = "Várias cidades"
                            modelo_trabalho = "Híbrido"
                        elif "no city" in local_lower:
                            localizacao = "Brasil (Remoto)"
                            modelo_trabalho = "Híbrido"
                        elif "hortolandia" in local_lower or "hortolândia" in local_lower:
                            localizacao = "Hortolândia"
                            modelo_trabalho = "Presencial"
                        
                        # Se não atende aos critérios, pula esta vaga
                        if localizacao is None:
                            continue
                        
                        dados_vaga = {
                            "empresa": "IBM",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo_trabalho,
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        vagas_encontradas_pagina += 1
                        print(f"  [VAGA VÁLIDA] {titulo} ({localizacao}) -> {modelo_trabalho}")
                    
                    except Exception as e:
                        print(f"  ⚠️ Erro ao processar uma vaga: {e}")
                        continue

                print(f"Total de vagas encontradas na página {page_num}: {vagas_encontradas_pagina}")
                
                # Verifica se existe botão "Próximo" e se não está desabilitado
                try:
                    next_button = page.locator('a[data-key="next"].cds--pagination-nav__page--direction')
                    
                    # Verifica se o botão existe
                    if next_button.count() == 0:
                        print("Botão de próxima página não encontrado. Fim da paginação.")
                        break
                    
                    # Verifica se o botão está desabilitado (tem a classe --disabled)
                    button_classes = next_button.get_attribute('class')
                    if 'cds--pagination-nav__page--disabled' in button_classes:
                        print("Botão de próxima página desabilitado. Fim da paginação.")
                        break
                    
                    # Rola até o botão e clica
                    print("Clicando em 'Próximo'...")
                    next_button.scroll_into_view_if_needed()
                    page.wait_for_timeout(1000)
                    next_button.click()
                    
                    # Aguarda carregamento da nova página
                    page.wait_for_load_state("networkidle", timeout=10000)
                    page.wait_for_timeout(2000)
                    page_num += 1
                    
                except Exception as e:
                    print(f"Erro ao tentar navegar para próxima página: {e}")
                    break

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da IBM: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---

