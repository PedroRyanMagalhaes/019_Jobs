import time
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da Sensedia.
    - Filtra ESTRITAMENTE por Campinas.
    - Classifica modelo baseado em 'Fully remote' ou 'Partially remote'.
    """
    
    url = EMPRESA_URLS.get("Sensedia")
    if not url:
        print("❌ URL da Sensedia não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://sensedia.hire.trakstar.com"

    print(f"Iniciando scraper para a Sensedia em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")
            
            try:
                page.wait_for_selector('.js-careers-page-job-list-item', timeout=10000)
            except:
                print("Nenhuma vaga encontrada inicialmente.")
                return []

            page_num = 1
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                cards = page.locator('.js-careers-page-job-list-item').all()
                print(f"Analisando {len(cards)} vagas nesta página.")

                for card in cards:
                    titulo_el = card.locator('.js-job-list-opening-name')
                    local_el = card.locator('.js-job-list-opening-loc')
                    meta_el = card.locator('.js-job-list-opening-meta')
                    
                    if titulo_el.count() == 0: continue

                    titulo = titulo_el.inner_text().strip()
                    localizacao_texto = local_el.inner_text().strip() if local_el.count() > 0 else ""
                    meta_texto = meta_el.inner_text().strip().lower() if meta_el.count() > 0 else ""
                    
                    # --- LÓGICA DE FILTRO E MODELO ATUALIZADA ---
                    
                    # 1. Filtro Rígido: Se não for de Campinas, ignora imediatamente.
                    if 'campinas' not in localizacao_texto.lower():
                        continue

                    # 2. Definição do Modelo (apenas para vagas de Campinas)
                    modelo = "Presencial" # Valor padrão se não achar info de remoto
                    
                    if 'fully remote' in meta_texto:
                        modelo = "Remoto"
                    elif 'partially remote' in meta_texto:
                        modelo = "Híbrido"
                    
                    # Link
                    link_relativo = card.get_attribute('data-href')
                    url_vaga = f"{base_url}{link_relativo}" if link_relativo else "Link não disponível"

                    dados_vaga = {
                        "empresa": "Sensedia",
                        "titulo": titulo,
                        "localizacao": localizacao_texto.replace("\n", " "),
                        "modelo_trabalho": modelo,
                        "url_vaga": url_vaga
                    }
                    vagas_para_salvar.append(dados_vaga)
                    print(f"  [VAGA VÁLIDA] {titulo} ({localizacao_texto}) -> {modelo}")

                # --- PAGINAÇÃO ---
                try:
                    next_li = page.locator('ul.pagination li.page-item').filter(has_text="Next")
                    if next_li.count() > 0:
                        class_attr = next_li.get_attribute("class")
                        if "disabled" in class_attr:
                            print("Botão 'Next' está desabilitado. Fim da paginação.")
                            break
                        else:
                            next_li.locator('a').click()
                            page.wait_for_load_state("networkidle", timeout=10000)
                            page_num += 1
                            time.sleep(1)
                    else:
                        break
                except Exception:
                    break
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Sensedia: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    import os
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA SENSEDIA EM MODO DE TESTE ---")
    
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Sensedia'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Sensedia selecionadas.")
        for vaga in vagas_coletadas:
            database.salvar_vaga(vaga)
        print(f"\nResumo: {len(vagas_coletadas)} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Sensedia foi selecionada no teste.")