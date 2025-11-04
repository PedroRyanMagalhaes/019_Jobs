from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da Lenovo usando 100% Playwright,
    com paginação e filtro de localização corretos.
    """
    
    url = EMPRESA_URLS.get("Lenovo")
    if not url:
        print("❌ URL da Lenovo não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://jobs.lenovo.com"

    print(f"Iniciando scraper para a Lenovo em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Estrutura da página carregada.")

            try:
                print("Procurando por banner de cookies...")
                cookie_button = page.get_by_role("button", name="Accept all", exact=True)
                cookie_button.click(timeout=10000)
                print("✅ Banner de cookies aceito.")
                page.wait_for_timeout(2000)
            except Exception:
                print("⚠️ Banner de cookies não encontrado ou já aceito.")

            page_num = 1
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                page.wait_for_selector('article.article--result', timeout=10000)
                vaga_items = page.locator('article.article--result').all()
                print(f"Analisando {len(vaga_items)} vagas encontradas.")

                if not vaga_items:
                    print("Nenhuma vaga encontrada nesta página.")
                    break

                for item in vaga_items:
                    link_tag = item.locator('h3 > a')
                    localizacao_tag = item.locator('div.article__header__text__subtitle > span').first
                    
                    if link_tag.count() > 0 and localizacao_tag.count() > 0:
                        titulo = link_tag.inner_text()
                        localizacao = localizacao_tag.inner_text()
                        url_vaga = link_tag.get_attribute('href')
                        
                        # --- FILTRO DE LOCALIZAÇÃO ATUALIZADO ---
                        local_lower = localizacao.lower()
                        if 'campinas' not in local_lower and 'indaiatuba' not in local_lower and 'jaguariuna' not in local_lower:
                            continue

                        dados_vaga = {
                            "empresa": "Lenovo",
                            "titulo": titulo.strip(),
                            "localizacao": localizacao.strip(),
                            "modelo_trabalho": "Híbrido",
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        print(f"  [VAGA VÁLIDA] {dados_vaga['titulo']} ({dados_vaga['localizacao']})")

                try:
                    # --- CORREÇÃO DA PAGINAÇÃO APLICADA AQUI ---
                    # Usamos .first() para clicar no primeiro botão "Next" encontrado
                    next_button = page.locator('a.paginationNextLink').first
                    
                    print("Clicando em 'Next >>'...")
                    next_button.click()
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    page_num += 1
                    
                except Exception as e:
                    print(f"Fim da paginação.")
                    break
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Lenovo: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA LENOVO EM MODO DE TESTE ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Lenovo'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Lenovo selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Lenovo foi selecionada no teste.")