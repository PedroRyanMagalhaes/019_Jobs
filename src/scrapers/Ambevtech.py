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
    Realiza o scraping das vagas da Ambev Tech (Gupy).
    - PRIORIDADE TOTAL: Aguarda e aceita cookies antes de qualquer interação.
    - Usa análise de texto completo para extrair título e local (independente da ordem das divs).
    - Filtra vagas de Campinas e Jaguariúna.
    """
    
    url = EMPRESA_URLS.get("Ambevtech")
    if not url:
        print("❌ URL da Ambevtech não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://ambevtech.gupy.io" 

    print(f"Iniciando scraper para a Ambev Tech em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", False) 
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="en-US", 
            viewport={"width": 800, "height": 600} 
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- ETAPA 1: PRIORIDADE TOTAL AOS COOKIES ---
            print("🛑 Aguardando carregamento do banner de cookies...")
            try:
                cookie_button = page.locator("#dm876A")
                # Espera explícita: Trava o script até o botão aparecer (max 15s)
                cookie_button.wait_for(state="visible", timeout=15000)
                cookie_button.click()
                print("✅ Banner de cookies aceito.")
                
                # Espera o banner sumir visualmente para liberar a tela
                cookie_button.wait_for(state="hidden", timeout=5000)
                print("Banner desapareceu. Caminho livre.")
            except Exception:
                print("⚠️ Banner de cookies não apareceu após espera (ou já foi aceito). Seguindo...")

            # Pequena pausa para garantir estabilidade antes do filtro
            page.wait_for_timeout(2000)

            # --- ETAPA 2: FILTRAR ESTADO ---
            try:
                print("Filtrando por Estado: São Paulo (SP)...")
                state_filter = page.get_by_label("State")
                state_filter.scroll_into_view_if_needed()
                state_filter.click()
                
                page.get_by_text("São Paulo (SP)", exact=True).click()
                print("✅ Estado selecionado. Aguardando recarregamento...")
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as e:
                print(f"❌ Erro ao filtrar o estado: {e}")
            
            # --- ETAPA 3: EXTRAÇÃO E PAGINAÇÃO ---
            page_num = 1
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                try:
                    page.wait_for_selector('li[data-testid="job-list__listitem"]', timeout=10000)
                except TimeoutError:
                    print("Nenhuma vaga encontrada na página (ou fim da lista).")
                    break
                
                vaga_items = page.locator('li[data-testid="job-list__listitem"]').all()
                print(f"Analisando {len(vaga_items)} vagas na página.")

                for item in vaga_items:
                    link_tag = item.locator('a[data-testid="job-list__listitem-href"]')
                    
                    # --- ESTRATÉGIA DE TEXTO COMPLETO ---
                    # Pega todo o texto do card para não depender da ordem das divs
                    texto_completo = link_tag.inner_text()
                    linhas = texto_completo.split('\n')
                    
                    texto_lower = texto_completo.lower()
                    
                    # Verifica se as cidades alvo estão no texto
                    if 'campinas' in texto_lower or 'jaguariúna' in texto_lower or 'jaguariuna' in texto_lower:
                        
                        # Tenta extrair o título (geralmente a 1ª linha)
                        titulo = linhas[0].strip() if linhas else "Título Desconhecido"
                        
                        # Tenta achar a linha específica da localização para salvar bonitinho
                        localizacao = "Localização não identificada"
                        for linha in linhas:
                            l_lower = linha.lower()
                            if 'campinas' in l_lower or 'jaguariúna' in l_lower or 'jaguariuna' in l_lower:
                                localizacao = linha.strip()
                                break
                        
                        url_relativa = link_tag.get_attribute('href')
                        url_vaga = f"{base_url}{url_relativa}"
                        
                        modelo = "Não informado"
                        if "hybrid" in texto_lower or "híbrido" in texto_lower:
                            modelo = "Híbrido"
                        elif "remote" in texto_lower or "remoto" in texto_lower:
                            modelo = "Remoto"
                        
                        dados_vaga = {
                            "empresa": "Ambev Tech",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo,
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        print(f"  [VAGA VÁLIDA] {titulo} ({localizacao}) -> {modelo}")

                # Paginação
                try:
                    next_button = page.locator('button[data-testid="pagination-next-button"]')
                    
                    if next_button.count() > 0:
                        next_button.scroll_into_view_if_needed()

                    if next_button.count() == 0 or next_button.is_disabled():
                        print("Fim da paginação.")
                        break
                    
                    print("Clicando em 'Próxima página'...")
                    next_button.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    page_num += 1
                except Exception:
                    print("Botão de próxima página não encontrado.")
                    break

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Ambev Tech: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
