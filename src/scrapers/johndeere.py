import time
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    VERSÃO FINAL: Separa a fase de carregamento da fase de extração para máxima estabilidade.
    """
    
    url = EMPRESA_URLS.get("JohnDeere")
    if not url:
        print("❌ URL da John Deere não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://careers.deere.com/careers/jobs/"

    print(f"Iniciando scraper para a John Deere em {url} (Modo Estável)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--start-maximized"],
            headless=SCRAPER_CONFIG.get("headless", True)
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent"),
            locale="pt-BR"
        )
        page = context.new_page()
        
        try:
            # --- FASE 1: CARREGAR TODAS AS VAGAS ---
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            scroll_container_selector = "div.position-sidebar-scroll-handler"
            
            print("Iniciando processo de scroll e clique para carregar tudo...")
            while True:
                try:
                    vagas_antes = page.locator('div.position-card').count()
                    page.locator(scroll_container_selector).hover()
                    for _ in range(5):
                        page.mouse.wheel(0, 1000)
                        time.sleep(0.3)
                    
                    show_more_button = page.locator('button.show-more-positions')
                    if show_more_button.count() == 0:
                         break

                    show_more_button.click(timeout=7000)
                    page.locator(f'div.position-card >> nth={vagas_antes}').wait_for(timeout=10000)
                except Exception:
                    print("Fim do carregamento de vagas.")
                    break

            # --- FASE 2: EXTRAIR DADOS UMA VAGA DE CADA VEZ ---
            print("\nIniciando extração de dados...")
            total_vagas = page.locator('div.position-card').count()
            print(f"Analisando {total_vagas} vagas encontradas.")

            for i in range(total_vagas):
                # A cada iteração, reencontramos o card pelo seu índice
                card = page.locator('div.position-card').nth(i)
                
                titulo = card.locator('div.position-title').inner_text()
                localizacao = card.locator('p.position-location').inner_text()
                
                local_lower = localizacao.lower()
                if 'indaiatuba' not in local_lower and 'campinas' not in local_lower:
                    continue

                print(f"Processando vaga {i+1}/{total_vagas}: {titulo}...")
                
                url_vaga = "Link não disponível"
                try:
                    card.click(timeout=5000)
                    page.wait_for_url('**/*pid=*', timeout=5000)
                    url_vaga = page.url
                except Exception:
                    print(f"  [AVISO] Não foi possível obter o link para esta vaga.")
                
                modelo = "Híbrido" 
                if card.locator('span.pills-module_label__yj2be').count() > 0:
                    modelo = card.locator('span.pills-module_label__yj2be').inner_text()

                dados_vaga = { "empresa": "John Deere", "titulo": titulo, "localizacao": localizacao, "modelo_trabalho": modelo, "url_vaga": url_vaga }
                vagas_para_salvar.append(dados_vaga)
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico: {e}")
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
    
    print(f"--- EXECUTANDO SCRAPER DA JOHN DEERE EM MODO DE TESTE ---")
    
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
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da John Deere foi selecionada no teste.")