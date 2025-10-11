import time
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da John Deere para o Brasil.
    - Clica em "Mostrar mais posições" e espera de forma inteligente o conteúdo carregar.
    - Extrai o HTML e usa BeautifulSoup para parsear os dados.
    - Filtra as vagas para Campinas e Indaiatuba.
    """
    
    url = EMPRESA_URLS.get("JohnDeere")
    if not url:
        print("❌ URL da John Deere não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://careers.deere.com/careers/jobs/"
    html_content = ""

    print(f"Iniciando scraper para a John Deere em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True)
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="pt-BR"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- LOOP DE CLIQUE COM ESPERA INTELIGENTE ---
            print("Procurando por botão 'Mostrar mais posições'...")
            while True:
                try:
                    # Conta quantas vagas existem ANTES do clique
                    vagas_antes = page.locator('div.position-card').count()
                    
                    show_more_button = page.locator('button.show-more-positions')
                    if show_more_button.count() == 0:
                         print("Botão não encontrado. Assumindo que todas as vagas foram carregadas.")
                         break

                    show_more_button.click(timeout=7000)
                    print(f"Botão clicado. Havia {vagas_antes} vagas. Aguardando novas vagas aparecerem...")

                    # ESPERA INTELIGENTE: Espera até que o número de vagas seja MAIOR que o anterior.
                    page.locator('div.position-card').nth(vagas_antes).wait_for(timeout=10000)
                    
                    vagas_depois = page.locator('div.position-card').count()
                    print(f"Novas vagas carregadas. Total agora: {vagas_depois}.")

                except Exception:
                    print("Não foi possível encontrar ou clicar no botão (ou novas vagas não carregaram). Fim da coleta.")
                    break
            
            print("Extraindo o HTML da lista de vagas...")
            list_container_html = page.locator('div[role="list"]').inner_html()
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da John Deere: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")

    html_content = list_container_html

    print("\nIniciando parse e aplicando regras de negócio...")
    soup = BeautifulSoup(html_content, 'html.parser')
    vagas_divs = soup.find_all('div', class_='position-card')
    print(f"Encontrados {len(vagas_divs)} vagas para analisar.")

    for vaga in vagas_divs:
        titulo_tag = vaga.find('div', class_='position-title')
        local_tag = vaga.find('p', class_='position-location')
        modelo_tag = vaga.find('span', class_='pills-module_label__yj2be')
        
        if not (titulo_tag and local_tag):
            continue

        titulo = titulo_tag.get_text(strip=True)
        localizacao = local_tag.get_text(strip=True)
        modelo = modelo_tag.get_text(strip=True) if modelo_tag else "Não informado"
        
        local_lower = localizacao.lower()
        if 'indaiatuba' not in local_lower and 'campinas' not in local_lower:
            continue

        job_id_attr = vaga.get('data-test-id', '')
        job_id = job_id_attr.split('-')[-1]
        url_vaga = f"{base_url}{job_id}" if job_id.isdigit() else "Link não disponível"

        dados_vaga = {
            "empresa": "John Deere", "titulo": titulo, "localizacao": localizacao,
            "modelo_trabalho": modelo, "url_vaga": url_vaga
        }
        vagas_para_salvar.append(dados_vaga)
        # print(f"  [VAGA VÁLIDA] {titulo} ({localizacao}) -> {modelo}") # Desativado para um log mais limpo

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA JOHN DEERE EM MODO DE TESTE ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

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
        print(f"\nResumo do Teste John Deere: {novas_vagas_salvas} novas vagas foram salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da John Deere foi selecionada no teste.")