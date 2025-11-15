import time
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping completo das vagas da Ypê (Gupy).
    - Aceita cookies
    - Filtra por SP
    - PULA a seleção de "itens por página" e vai direto para a paginação.
    """
    
    url = EMPRESA_URLS.get("Ype")
    if not url:
        print("❌ URL da Ypê não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://carreirasype.gupy.io" 

    print(f"Iniciando scraper para a Ypê em {url} (Forçando idioma Inglês)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True) 
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="en-US" # Força o idioma Inglês
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- ETAPA 1: ACEITAR COOKIES ---
            print("Procurando por banner de cookies...")
            cookie_button = page.locator("#dm876A")
            cookie_button.wait_for(state="visible", timeout=10000)
            cookie_button.click()
            print("✅ Banner de cookies aceito.")
            
            print("Aguardando página recarregar após o aceite dos cookies...")
            page.wait_for_load_state("networkidle", timeout=15000)
            print("✅ Página recarregada.")

            # --- ETAPA 2: FILTRAR ESTADO ---
            print("Filtrando por Estado: São Paulo (SP)...")
            state_filter = page.get_by_label("State")
            state_filter.click()
            page.get_by_text("São Paulo (SP)", exact=True).click()
            print("✅ Estado selecionado. Aguardando recarregamento...")
            page.wait_for_load_state("networkidle", timeout=10000)
            print("Lista de vagas pronta (com 10 por página).")

            # --- ETAPA 3: REMOVIDA ---
            print("Ignorando seleção de '50 por página' e indo direto para a paginação.")

            # --- ETAPA 4: EXTRAÇÃO E PAGINAÇÃO ---
            page_num = 1
            while True:
                print(f"\n--- Processando Página {page_num} ---")
                
                try:
                    page.wait_for_selector('li[data-testid="job-list__listitem"]', timeout=10000)
                except TimeoutError:
                    print("Nenhuma vaga encontrada na página. Encerrando.")
                    break
                
                vaga_items = page.locator('li[data-testid="job-list__listitem"]').all()
                print(f"Analisando {len(vaga_items)} vagas na página.")

                for item in vaga_items:
                    link_tag = item.locator('a[data-testid="job-list__listitem-href"]')
                    titulo_tag = link_tag.locator('div.sc-d1f2599d-2')
                    local_tag = link_tag.locator('div.sc-d1f2599d-3')
                    
                    if titulo_tag.count() == 0 or local_tag.count() == 0:
                        continue

                    titulo = titulo_tag.inner_text()
                    localizacao = local_tag.inner_text()
                    
                    local_lower = localizacao.lower()
                    if 'campinas' in local_lower:
                        
                        url_relativa = link_tag.get_attribute('href')
                        url_vaga = f"{base_url}{url_relativa}"
                        
                        modelo = "Não informado"
                        if "hybrid" in local_lower:
                            modelo = "Híbrido"
                        
                        dados_vaga = {
                            "empresa": "Ype",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo,
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        print(f"  [VAGA VÁLIDA] {titulo} ({localizacao})")

                try:
                    next_button = page.locator('button[data-testid="pagination-next-button"]')
                    if next_button.is_disabled():
                        print("Fim da paginação (botão desabilitado).")
                        break
                    
                    print("Clicando em 'Próxima página'...")
                    next_button.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    page_num += 1
                except Exception:
                    print("Fim da paginação (botão não encontrado).")
                    break

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Ypê: {e}")
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
    
    print(f"--- EXECUTANDO SCRAPER DA YPÊ EM MODO DE TESTE (EM INGLÊS) ---")
    
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Ype'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Ypê selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Ypê foi selecionada no teste.")