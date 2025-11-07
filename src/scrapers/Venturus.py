import time
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import re

def raspar():
    """
    Realiza o scraping das vagas da Venturus, usando scroll para carregar todas.
    Extrai localização e modelo diretamente do texto do título da vaga.
    """
    
    url = EMPRESA_URLS.get("Venturus")
    if not url:
        print("❌ URL da Venturus não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://venturus.inhire.app"

    print(f"Iniciando scraper para a Venturus em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- LÓGICA DE SCROLL INFINITO ADICIONADA ---
            print("Iniciando scroll para carregar todas as vagas...")
            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                try:
                    # Espera um pouco para o site carregar o novo conteúdo
                    page.wait_for_timeout(2000) 
                except TimeoutError:
                    pass
                
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    print("Fim da página alcançado. Todas as vagas carregadas.")
                    break
                last_height = new_height
                print("Scroll realizado, carregando mais...")
            # ---------------------------------------------

            # Espera final para garantir que a última leva renderizou
            page.wait_for_selector('li[data-sentry-component="JobPosition"]', timeout=10000)

            vaga_items = page.locator('li[data-sentry-component="JobPosition"]').all()
            print(f"Analisando {len(vaga_items)} vagas encontradas.")

            for item in vaga_items:
                titulo_bruto_el = item.locator('div[data-sentry-element="JobPositionName"]')
                if titulo_bruto_el.count() == 0: continue
                titulo_bruto = titulo_bruto_el.inner_text().strip()

                link_el = item.locator('a[data-component-name="job-position-link"]')
                url_relativa = link_el.get_attribute('href') or ""
                
                if url_relativa.startswith("http"):
                     url_vaga = url_relativa
                else:
                     url_vaga = f"{base_url}{url_relativa}"

                # --- LÓGICA DE PARSE DO TÍTULO ---
                modelo = "Não informado"
                localizacao = "Não informado"
                titulo_limpo = titulo_bruto

                match = re.search(r'\(([^)]+)\)$', titulo_bruto)
                if match:
                    info_extra = match.group(1)
                    titulo_limpo = titulo_bruto.replace(f"({info_extra})", "").strip()
                    
                    if 'remoto' in info_extra.lower():
                        modelo = "Remoto"
                        localizacao = "Remoto"
                    elif 'híbrido' in info_extra.lower():
                        modelo = "Híbrido"
                        partes = info_extra.split('-')
                        if len(partes) > 1:
                             localizacao = partes[1].strip()
                        else:
                             localizacao = info_extra
                    else:
                        localizacao = info_extra

                # --- FILTRO DE NEGÓCIO ---
                eh_remoto = modelo == "Remoto"
                eh_campinas_hibrido = (modelo == "Híbrido" and "campinas" in localizacao.lower())

                if eh_remoto or eh_campinas_hibrido:
                    dados_vaga = {
                        "empresa": "Venturus",
                        "titulo": titulo_limpo,
                        "localizacao": localizacao,
                        "modelo_trabalho": modelo,
                        "url_vaga": url_vaga
                    }
                    vagas_para_salvar.append(dados_vaga)
                    print(f"  [VAGA VÁLIDA] {titulo_limpo} ({localizacao}) -> {modelo}")

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Venturus: {e}")
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
    
    print(f"--- EXECUTANDO SCRAPER DA VENTURUS EM MODO DE TESTE ---")

    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Venturus'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Venturus selecionadas.")
        for vaga in vagas_coletadas:
            database.salvar_vaga(vaga)
        print(f"Resumo: {len(vagas_coletadas)} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Venturus foi selecionada no teste.")