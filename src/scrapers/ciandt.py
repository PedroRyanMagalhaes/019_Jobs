import time
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    VERSÃO DE PRODUÇÃO: Captura a lista correta de vagas e aplica a lógica de negócio final.
    """
    
    url = EMPRESA_URLS.get("CI&T")
    cookie_file_path = "data/ciandt_cookies.json"
    if not url or not os.path.exists(cookie_file_path):
        print(f"❌ ERRO: URL da CI&T ou arquivo de cookies '{cookie_file_path}' não encontrado.")
        return []

    vagas_para_salvar = []
    base_url = "https://ciandt.com"
    html_content = ""

    print(f"Iniciando scraper para a CI&T em {url} (MODO DE PRODUÇÃO)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome", 
            headless=SCRAPER_CONFIG.get("headless", True) # Pode voltar para True em produção
        )
        context = browser.new_context(
            storage_state=cookie_file_path,
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="pt-BR"
        )
        page = context.new_page()
        
        try:
            page.goto(url, timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("Página carregada. Procurando por modais...")

            try:
                page.get_by_role("button", name="Sim, eu aceito cookies da CI&T", exact=True).click(timeout=7000)
                print("✅ Banner de cookies aceito.")
                page.wait_for_timeout(1000)
            except Exception:
                print("⚠️ Banner de cookies não encontrado ou já aceito.")

            try:
                page.get_by_role("button", name="OK", exact=True).click(timeout=5000)
                print("✅ Botão 'OK' clicado.")
                page.wait_for_timeout(2000)
            except Exception:
                print("⚠️ Modal com botão 'OK' não encontrado.")
            
            print("Iniciando scroll...")
            last_height = 0
            for i in range(20):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    print(f"Fim da página alcançado no scroll {i+1}.")
                    break
                last_height = new_height
            
            print("Extraindo o HTML final da página...")
            html_content = page.content()
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da CI&T: {e}")
        finally:
            if browser and browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")

    if not html_content:
        return []

    print("\nIniciando parse e aplicando regras de negócio...")
    soup = BeautifulSoup(html_content, 'html.parser')
    vagas_divs = soup.find_all('div', class_='opprtunity-item')
    print(f"Encontrados {len(vagas_divs)} vagas para analisar.")

    for vaga in vagas_divs:
        titulo_tag = vaga.find('h2', class_='wp-block-cit-block-ciandt-heading')
        local_tag = vaga.find('div', class_='wp-block-cit-block-ciandt-short-text')
        link_tag = vaga.find('a', class_='wp-block-cit-block-ciandt-link')

        if not all([titulo_tag, local_tag, link_tag]):
            continue

        titulo = titulo_tag.get_text(strip=True)
        local_full = local_tag.find('span').get_text(strip=True)
        local = local_full.split('-')[-1].strip()
        url_vaga = link_tag.get('href', '')
        if not url_vaga.startswith('http'):
            url_vaga = f"{base_url}{url_vaga}"
        
        # --- LÓGICA DE NEGÓCIO FINAL ---
        modelo_trabalho = ""
        local_lower = local.lower()

        if 'campinas' in local_lower:
            modelo_trabalho = "Híbrido"
        elif 'brazil' in local_lower or 'brasil' in local_lower:
            modelo_trabalho = "Remoto/Híbrido"
        else:
            # Se não for Campinas nem Brazil, ignora a vaga
            continue
        
        dados_vaga = {
            "empresa": "CI&T",
            "titulo": titulo, # Título completo, como pedido
            "localizacao": local,
            "modelo_trabalho": modelo_trabalho,
            "url_vaga": url_vaga
        }
        vagas_para_salvar.append(dados_vaga)
        print(f"  [VAGA VÁLIDA] {titulo} ({local}) -> {modelo_trabalho}")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA CI&T EM MODO DE PRODUÇÃO ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")

    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'CI&T'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da CI&T selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo do Teste CI&T: {novas_vagas_salvas} novas vagas foram salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da CI&T foi selecionada no teste.")