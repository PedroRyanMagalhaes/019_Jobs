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
    Realiza o scraping completo das vagas do Instituto Eldorado (Gupy).
    - Aceita cookies
    - Extrai todas as vagas
    - Filtra por:
      * Vagas que contenham "Campinas" na localização
      * Vagas "Remote Work" (trabalho remoto puro)
    - Pagina por todas as páginas disponíveis.
    """
    
    url = EMPRESA_URLS.get("Eldorado")
    if not url:
        print("❌ URL do Eldorado não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://institutoeldorado.gupy.io" 

    print(f"Iniciando scraper para o Eldorado em {url} (Forçando idioma Inglês)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True) 
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="en-US" # Força o idioma Inglês
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- ETAPA 1: ACEITAR COOKIES ---
            print("Procurando por banner de cookies...")
            try:
                cookie_button = page.locator("#dm876A")
                cookie_button.wait_for(state="visible", timeout=10000)
                cookie_button.click()
                print("✅ Banner de cookies aceito.")
                
                print("Aguardando página recarregar após o aceite dos cookies...")
                page.wait_for_load_state("networkidle", timeout=15000)
                print("✅ Página recarregada.")
            except Exception as e:
                print(f"⚠️ Banner de cookies não encontrado ou já aceito: {e}")

            # --- ETAPA 2: EXTRAÇÃO E PAGINAÇÃO ---
            page_num = 1
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                try:
                    page.wait_for_selector('li[data-testid="job-list__listitem"]', timeout=10000)
                except TimeoutError:
                    print("Nenhuma vaga encontrada na página. Encerrando.")
                    break
                
                vaga_items = page.locator('li[data-testid="job-list__listitem"]').all()
                print(f"Analisando {len(vaga_items)} vagas na página.")

                for item in vaga_items:
                    link_tag = item.locator('a[data-testid="job-list__listitem-href"]')
                    titulo_tag = link_tag.locator('div.sc-d1f2599d-2')
                    local_tag = link_tag.locator('div.sc-d1f2599d-3')
                    
                    if titulo_tag.count() == 0 or local_tag.count() == 0:
                        continue

                    titulo = titulo_tag.inner_text()
                    localizacao = local_tag.inner_text()
                    
                    local_lower = localizacao.lower().strip()
                    
                    # Lógica de filtragem:
                    # 1. Aceita se contém "campinas"
                    # 2. Aceita se é exatamente "remote work"
                    # 3. Rejeita todo o resto
                    
                    aceitar = False
                    modelo = "Não informado"
                    
                    if 'campinas' in local_lower:
                        aceitar = True
                        # Determinar modelo de trabalho
                        if "hybrid" in local_lower:
                            modelo = "Híbrido"
                        elif "remote" in local_lower:
                            modelo = "Remoto"
                        else:
                            modelo = "Presencial"
                    elif local_lower == "remote work":
                        aceitar = True
                        modelo = "Remoto"
                    
                    if aceitar:
                        url_relativa = link_tag.get_attribute('href')
                        url_vaga = f"{base_url}{url_relativa}"
                        
                        dados_vaga = {
                            "empresa": "Eldorado",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo,
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        print(f"  [VAGA VÁLIDA] {titulo} ({localizacao})")

                # Tentar ir para a próxima página
                try:
                    next_button = page.locator('button[data-testid="pagination-next-button"]')
                    if next_button.is_disabled():
                        print("Fim da paginação (botão desabilitado).")
                        break
                    
                    print("Clicando em 'Próxima página'...")
                    next_button.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    page_num += 1
                except Exception:
                    print("Fim da paginação (botão não encontrado).")
                    break

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper do Eldorado: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---

