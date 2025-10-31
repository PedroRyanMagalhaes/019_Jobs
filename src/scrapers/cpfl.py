#TODO: NÂO TA INDO PARA PAGINA 2 DAS VAGAS QUANDO TEM


import time
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    VERSÃO DE PRODUÇÃO: Usa a estratégia com BeautifulSoup e paginação por número de página.
    """
    
    url = EMPRESA_URLS.get("Cpfl")
    if not url:
        print("❌ URL da CPFL não encontrada nas configurações.")
        return []

    vagas_encontradas = []
    base_url = "https://vagas.cpfl.com.br"

    print(f"Iniciando scraper para a CPFL em {url} (MODO DE PRODUÇÃO)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True),
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page(user_agent=SCRAPER_CONFIG.get("user_agent"))
        
        try:
            page.goto(url, timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("Aguardando a página carregar completamente (networkidle)...")
            page.wait_for_load_state('networkidle', timeout=20000)
            print("✅ Página inicial carregada.")

            page_num = 1
            while True:
                print(f"--- Processando Página {page_num} ---")

                tabela_html = page.locator('table#searchresults > tbody').inner_html()
                soup = BeautifulSoup(tabela_html, 'html.parser')
                vagas_tr = soup.find_all('tr', class_='data-row')
                print(f"Encontrados {len(vagas_tr)} vagas na página {page_num}.")

                if not vagas_tr:
                    print("Nenhuma vaga encontrada na página, encerrando.")
                    break

                for vaga_tr in vagas_tr:
                    titulo_tag = vaga_tr.find('a', class_='jobTitle-link')
                    localizacao_tag = None
                    
                    desktop_container = vaga_tr.find('td', class_='colLocation')
                    if desktop_container:
                        localizacao_tag = desktop_container.find('span', class_='jobLocation')

                    if not localizacao_tag or not localizacao_tag.get_text(strip=True):
                        mobile_container = vaga_tr.find('div', class_='visible-phone')
                        if mobile_container:
                            localizacao_tag = mobile_container.find('span', class_='jobLocation')

                    if titulo_tag and localizacao_tag:
                        titulo = titulo_tag.get_text(strip=True)
                        url_relativa = titulo_tag['href']
                        url_vaga = f"{base_url}{url_relativa}"
                        localizacao = localizacao_tag.get_text(strip=True)

                        if not localizacao: continue

                        dados_vaga = { "empresa": "CPFL", "titulo": titulo, "localizacao": localizacao, "modelo_trabalho": "Não informado", "url_vaga": url_vaga }
                        vagas_encontradas.append(dados_vaga)
                
                # --- LÓGICA DE PAGINAÇÃO FINAL: POR NÚMERO DA PÁGINA ---
                try:
                    next_page_num_str = str(page_num + 1)
                    print(f"Procurando link para a página '{next_page_num_str}'...")

                    # Procura o link cujo texto é exatamente o número da próxima página
                    next_page_link = page.get_by_role("link", name=next_page_num_str, exact=True)
                    
                    next_page_link.click(timeout=5000)
                    
                    print(f"Navegando para a página {next_page_num_str}...")
                    page.wait_for_load_state('networkidle', timeout=20000)
                    page_num += 1
                except (TimeoutError, Exception):
                    print(f"Link para a página {page_num + 1} não encontrado. Fim da coleta.")
                    break
        
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da CPFL: {e}")
        finally:
            if browser and browser.is_connected():
                browser.close()
            print("Scraper da CPFL finalizado.")

    print(f"\nColeta bruta finalizada. Total de {len(vagas_encontradas)} vagas encontradas em todas as páginas.")
    print("Aplicando filtro para vagas em 'Campinas, BR'...")

    vagas_filtradas = [ v for v in vagas_encontradas if v.get('localizacao', '').strip().lower() == 'campinas, br' ]
    
    print(f"Filtro aplicado. {len(vagas_filtradas)} vagas de Campinas serão retornadas.")
    return vagas_filtradas

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    import os

    os.makedirs("data", exist_ok=True)
    TEST_DB_FILE = "data/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA CPFL EM MODO DE TESTE (PRODUÇÃO) ---")


# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    import os

    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA CPFL EM MODO DE TESTE (PRODUÇÃO) ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'CPFL'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da CPFL (pós-filtro) encontradas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo do Teste CPFL: {novas_vagas_salvas} novas vagas foram salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da CPFL (pós-filtro) foi encontrada no teste.")