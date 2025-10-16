from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da Dell, com o seletor de vagas corrigido.
    """
    
    url = EMPRESA_URLS.get("Dell")
    if not url:
        print("❌ URL da Dell não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://jobs.dell.com"

    print(f"Iniciando scraper para a Dell em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        context.grant_permissions([], origin=url)
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Estrutura da página carregada.")

            try:
                print("Procurando por banner de cookies...")
                cookie_button = page.locator("#igdpr-button")
                cookie_button.click(timeout=10000)
                print("✅ Banner de cookies aceito.")
                page.wait_for_timeout(2000)
            except Exception:
                print("⚠️ Banner de cookies não encontrado ou já aceito.")

            print("\nIniciando análise das vagas...")
            
            # --- SELETOR CORRIGIDO AQUI ---
            # Removemos os '>' para um seletor mais flexível que encontra os <li> em qualquer nível
            vaga_items = page.locator('section.jobs-list li').all()
            print(f"Analisando {len(vaga_items)} vagas encontradas.")

            for item in vaga_items:
                link_tag = item.locator('a')
                
                # Verifica se os elementos existem antes de tentar extrair o texto
                if link_tag.locator('h2').count() > 0 and link_tag.locator('span.job-location').count() > 0:
                    titulo = link_tag.locator('h2').inner_text()
                    localizacao = link_tag.locator('span.job-location').inner_text()
                    url_relativa = link_tag.get_attribute('href')
                    url_vaga = f"{base_url}{url_relativa}"
                    
                    dados_vaga = {
                        "empresa": "Dell",
                        "titulo": titulo,
                        "localizacao": localizacao.strip().replace('\xa0', ' '), # Limpa espaços extras
                        "modelo_trabalho": "Não informado",
                        "url_vaga": url_vaga
                    }
                    vagas_para_salvar.append(dados_vaga)
                    print(f"  [VAGA VÁLIDA] {titulo} ({dados_vaga['localizacao']})")
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Dell: {e}")
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
    
    print(f"--- EXECUTANDO SCRAPER DA DELL EM MODO DE TESTE ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Dell'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Dell selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Dell foi selecionada no teste.")