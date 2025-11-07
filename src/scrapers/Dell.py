from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da Dell, com seletor corrigido baseado no ID da seção.
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
        # Nega permissão de geolocalização para evitar pop-ups
        context.grant_permissions([], origin=url)
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Estrutura da página carregada.")

            # --- TENTATIVA DE ACEITAR COOKIES ---
            try:
                print("Procurando por banner de cookies...")
                cookie_button = page.locator("#igdpr-button")
                if cookie_button.is_visible(timeout=5000):
                    cookie_button.click()
                    print("✅ Banner de cookies aceito.")
                    page.wait_for_timeout(2000) # Espera a página reagir
                else:
                     print("⚠️ Banner de cookies não apareceu.")
            except Exception:
                print("⚠️ Erro ao tentar interagir com banner de cookies (pode já ter sido aceito).")

            print("\nIniciando análise das vagas...")
            
            # --- CORREÇÃO PRINCIPAL: NOVO SELETOR E ESPERA ---
            # O seletor agora usa o ID que você mostrou no print: #search-results-list
            seletor_vagas = '#search-results-list ul > li'
            
            try:
                # Espera até que pelo menos uma vaga seja visível na tela
                print("Aguardando a lista de vagas carregar...")
                page.wait_for_selector(seletor_vagas, timeout=20000)
            except TimeoutError:
                 print("❌ Timeout: A lista de vagas não carregou. Pode não haver vagas para este filtro.")
                 return []

            vaga_items = page.locator(seletor_vagas).all()
            print(f"Analisando {len(vaga_items)} vagas encontradas.")

            for item in vaga_items:
                # Verifica se é um item de vaga real (tem que ter um link <a> dentro)
                link_tag = item.locator('a').first
                if link_tag.count() == 0:
                    continue
                
                titulo_tag = link_tag.locator('h2')
                localizacao_tag = link_tag.locator('span.job-location')

                if titulo_tag.count() > 0 and localizacao_tag.count() > 0:
                    titulo = titulo_tag.inner_text().strip()
                    localizacao = localizacao_tag.inner_text().strip()
                    url_relativa = link_tag.get_attribute('href')
                    url_vaga = f"{base_url}{url_relativa}" if not url_relativa.startswith('http') else url_relativa
                    
                    dados_vaga = {
                        "empresa": "Dell",
                        "titulo": titulo,
                        "localizacao": localizacao,
                        "modelo_trabalho": "Não informado",
                        "url_vaga": url_vaga
                    }
                    vagas_para_salvar.append(dados_vaga)
                    print(f"  [VAGA VÁLIDA] {titulo} ({localizacao})")
            
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