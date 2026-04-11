# Scraper atualizado para a nova estrutura do site John Deere (2026)

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
    VERSÃO ATUALIZADA: Adaptado para a nova estrutura do site John Deere.
    """
    
    url = EMPRESA_URLS.get("Johndeere")
    if not url:
        print("❌ URL da John Deere não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://careers.deere.com"

    print(f"Iniciando scraper para a John Deere em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--start-maximized"],
            headless=SCRAPER_CONFIG.get("headless", True)
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="pt-BR"
        )
        page = context.new_page()
        
        try:
            # --- NAVEGAÇÃO E EXTRAÇÃO POR PÁGINA ---
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")
            time.sleep(2)  # Aguarda carregamento inicial
            
            pagina_numero = 1
            
            while True:
                print(f"\n{'='*50}")
                print(f"PROCESSANDO PÁGINA {pagina_numero}")
                print(f"{'='*50}\n")
                
                # Aguarda os cards carregarem
                page.wait_for_selector('div.cardContainer-GcY1a', timeout=10000)
                time.sleep(1)
                
                # Extrai vagas da página atual
                cards = page.locator('div.cardContainer-GcY1a').all()
                print(f"Encontrados {len(cards)} cards nesta página.\n")

                for i, card in enumerate(cards):
                    try:
                        # Extrai título
                        titulo_elem = card.locator('div.title-1aNJK')
                        if titulo_elem.count() == 0:
                            continue
                        titulo = titulo_elem.inner_text()
                        
                        # Extrai localização
                        localizacao_elem = card.locator('div.fieldValue-3kEar').first
                        if localizacao_elem.count() == 0:
                            continue
                        localizacao = localizacao_elem.inner_text()
                        
                        # Filtra apenas Indaiatuba e Campinas
                        local_lower = localizacao.lower()
                        if 'indaiatuba' not in local_lower and 'campinas' not in local_lower:
                            continue

                        print(f"  ✓ {titulo}")
                        
                        # Extrai URL da vaga
                        link_elem = card.locator('a.card-F1ebU')
                        url_vaga = "Link não disponível"
                        if link_elem.count() > 0:
                            href = link_elem.get_attribute('href')
                            if href:
                                url_vaga = base_url + href if href.startswith('/') else href
                        
                        # Extrai modelo de trabalho (se existir o selo)
                        modelo = "Híbrido"  # Padrão
                        modelo_elem = card.locator('span.pills-module_label__yj2be')
                        if modelo_elem.count() > 0:
                            modelo = modelo_elem.inner_text()

                        dados_vaga = {
                            "empresa": "John Deere",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo,
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        
                    except Exception as e:
                        print(f"  [AVISO] Erro ao processar card {i+1}: {e}")
                        continue
                
                # Verifica paginação
                pager = page.locator('div.pagination-module_page-tracker__Dhok2 span')
                if pager.count() >= 3:
                    pagina_atual = pager.nth(0).inner_text()
                    total_paginas = pager.nth(2).inner_text()
                    print(f"\n📄 Página {pagina_atual} de {total_paginas}")
                    
                    if pagina_atual == total_paginas:
                        print("✅ Última página confirmada!")
                        break
                
                # Verifica se há próxima página - botão com seletor mais robusto
                next_button = page.locator('button.pagination-module_pagination-next__OHCf9')
                
                if next_button.count() == 0:
                    print("\n✅ Botão 'Next' não encontrado. Fim da navegação.")
                    break
                
                is_disabled = next_button.get_attribute('aria-disabled')
                if is_disabled == 'true':
                    print("\n✅ Última página alcançada (botão desabilitado).")
                    break
                
                # Faz scroll até o botão e clica
                print("\n➡️  Avançando para próxima página...")
                try:
                    next_button.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    next_button.click()
                    time.sleep(2.5)  # Aguarda carregamento
                    pagina_numero += 1
                except Exception as e:
                    print(f"❌ Erro ao clicar no botão Next: {e}")
                    break
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\n✅ Análise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA JOHN DEERE EM MODO DE TESTE ---")
    
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'John Deere'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da John Deere selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da John Deere foi selecionada no teste.")