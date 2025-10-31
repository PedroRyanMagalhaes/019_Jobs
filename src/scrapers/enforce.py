#OK

from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da Enforce. A URL já é o conteúdo do iframe.
    """
    
    url = EMPRESA_URLS.get("Enforce")
    if not url:
        print("❌ URL da Enforce não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    html_content = ""

    print(f"Iniciando scraper para a Enforce em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- CORREÇÃO APLICADA: LÓGICA DE IFRAME REMOVIDA ---
            # Buscamos o contêiner diretamente na página
            print("Extraindo o HTML da lista de vagas...")
            html_content = page.locator('.job-posts').inner_html()
            
        except TimeoutError:
            print("❌ Timeout: O contêiner de vagas (com a classe 'job-posts') não foi encontrado a tempo.")
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Enforce: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")

    if not html_content:
        return []

    print("\nIniciando parse e aplicando regras de negócio...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    vagas_tr = soup.find_all('tr', class_='job-post')
    print(f"Encontrados {len(vagas_tr)} vagas para analisar.")

    for vaga in vagas_tr:
        link_tag = vaga.find('a')
        if not link_tag:
            continue

        url_vaga = link_tag.get('href', '')
        titulo_tag = link_tag.find('p', class_='body--medium')
        localizacao_tag = link_tag.find('p', class_='body__secondary')

        if not (titulo_tag and localizacao_tag):
            continue

        titulo = titulo_tag.get_text(strip=True)
        localizacao = localizacao_tag.get_text(strip=True)
        
        # O filtro agora vai pegar "Campinas" e "São Paulo ou Campinas"
        if 'campinas' in localizacao.lower():
            dados_vaga = {
                "empresa": "Enforce",
                "titulo": titulo,
                "localizacao": localizacao,
                "modelo_trabalho": "Presencial",
                "url_vaga": url_vaga
            }
            vagas_para_salvar.append(dados_vaga)
            print(f"  [VAGA VÁLIDA] {titulo} ({localizacao})")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA ENFORCE EM MODO DE TESTE ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Enforce'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Enforce selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Enforce foi selecionada no teste.")