import time
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG

def raspar():
    """
    Realiza o scraping de TODAS as vagas da CPFL e depois filtra por Campinas.
    - Navega por todas as páginas de resultados.
    - Extrai título, URL e localização de cada vaga.
    - Filtra a lista final em Python para manter apenas vagas de Campinas.
    """
    
    url = EMPRESA_URLS.get("CPFL")
    if not url:
        print("❌ URL da CPFL não encontrada nas configurações.")
        return []

    vagas_encontradas = []
    base_url = "https://vagas.cpfl.com.br"

    print(f"Iniciando scraper para a CPFL em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True),
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page(user_agent=SCRAPER_CONFIG.get("user_agent"))
        
        try:
            page.goto(url, timeout=SCRAPER_CONFIG.get("timeout", 60000))
            
            print("✅ Página inicial carregada. Iniciando coleta de todas as vagas.")

            while True:
                print("Coletando informações da página atual...")
                page.wait_for_selector('table#searchresults', state='visible', timeout=10000)
                
                vagas_na_pagina = page.locator('tr.data-row').all()
                print(f"Encontrados {len(vagas_na_pagina)} elementos de vagas na página.")
                
                if not vagas_na_pagina:
                    print("Nenhuma vaga encontrada na página. Encerrando coleta.")
                    break

                for vaga_tr in vagas_na_pagina:
                    link_element = vaga_tr.locator('a.jobTitle-link').first
                    titulo = link_element.inner_text().strip()
                    url_relativa = link_element.get_attribute('href')
                    url_vaga = f"{base_url}{url_relativa}"
                    
                    # --- SOLUÇÃO DEFINITIVA PARA LOCALIZAÇÃO ---
                    # Usando um seletor específico que só existe na versão desktop para evitar qualquer ambiguidade.
                    localizacao = vaga_tr.locator('td.collocation > span.joblocation').inner_text().strip()

                    dados_vaga = {
                        "empresa": "CPFL",
                        "titulo": titulo,
                        "localizacao": localizacao,
                        "modelo_trabalho": "Não informado",
                        "url_vaga": url_vaga,
                    }
                    vagas_encontradas.append(dados_vaga)

                try:
                    next_button = page.locator('a.next')
                    if next_button.get_attribute('aria-disabled') == 'true' or not next_button.is_visible(timeout=3000):
                        print("Fim da paginação. Não há mais páginas.")
                        break
                    else:
                        print("Navegando para a próxima página...")
                        next_button.click()
                except (TimeoutError, Exception):
                    print("Botão 'Next' não encontrado ou erro na navegação. Fim da coleta.")
                    break
        
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado no scraper da CPFL: {e}")
        finally:
            if browser and browser.is_connected():
                browser.close()
            print("Scraper da CPFL finalizado.")

    print(f"\nColeta bruta finalizada. Total de {len(vagas_encontradas)} vagas encontradas.")
    print("Aplicando filtro para vagas em 'Campinas, BR'...")

    vagas_filtradas = [
        vaga for vaga in vagas_encontradas 
        if vaga.get('localizacao', '').strip().lower() == 'campinas, br'
    ]
    
    print(f"Filtro aplicado. {len(vagas_filtradas)} vagas de Campinas serão retornadas.")
    
    return vagas_filtradas

# --- BLOCO DE TESTE (NÃO PRECISA DE ALTERAÇÃO) ---
if __name__ == "__main__":
    from src.database import database
    import os

    os.makedirs("data", exist_ok=True)
    TEST_DB_FILE = "data/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA CPFL EM MODO DE TESTE COMPLETO ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

    database.inicializar_banco()
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