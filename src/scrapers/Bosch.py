#OK

# Ajusta o path quando executado diretamente
if __name__ == "__main__":
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))

import time
import random
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG

def raspar():
    """
    Realiza o scraping das vagas da Bosch para a localidade de Campinas.
    - Clica em "Mostrar mais empregos" para carregar todas as vagas.
    - Extrai título, URL, e outros dados relevantes.
    """
    
    url = EMPRESA_URLS.get("Bosch")
    if not url:
        print("❌ URL da Bosch não encontrada nas configurações.")
        return []

    vagas_encontradas = []

    print(f"Iniciando scraper para a Bosch em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True),
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page(user_agent=SCRAPER_CONFIG.get("user_agent"))
        
        try:
            page.goto(url, timeout=SCRAPER_CONFIG.get("timeout", 3000))
            page.wait_for_load_state('domcontentloaded')

            print("Procurando pela seção de vagas de Campinas...")
            # Busca todas as seções de Campinas (pode haver múltiplas devido a capitalização diferente)
            campinas_sections = page.locator("section.openings-section").filter(has_text="Campinas, Brasil")
            
            sections_count = campinas_sections.count()
            if sections_count == 0:
                print("⚠️ Seção de Campinas não encontrada na página. Encerrando scraper da Bosch.")
                browser.close()
                return []
            
            print(f"✅ {sections_count} seção(ões) de Campinas encontrada(s).")

            # Processa cada seção de Campinas encontrada
            for section_index in range(sections_count):
                campinas_section = campinas_sections.nth(section_index)
                print(f"\n--- Processando seção {section_index + 1} de {sections_count} ---")
                
                # Clica em "Mostrar mais" para carregar todas as vagas desta seção
                while True:
                    try:
                        show_more_button = campinas_section.get_by_role("link", name="Mostrar mais empregos")
                        
                        if show_more_button.is_visible(timeout=5000):
                            print("Carregando mais vagas...")
                            show_more_button.click()
                            time.sleep(random.uniform(1.5, 2.5))
                        else:
                            print("Botão 'Mostrar mais' não está mais visível.")
                            break
                    except Exception:
                        print("Todas as vagas desta seção foram carregadas.")
                        break

                print("Coletando informações das vagas...")
                lista_vagas_li = campinas_section.locator("li.opening-job")
                count = lista_vagas_li.count()
                print(f"Encontrados {count} elementos de vagas nesta seção.")

                for i in range(count):
                    vaga_li = lista_vagas_li.nth(i)
                    
                    titulo_vaga_element = vaga_li.locator("h4.job-title")
                    link_vaga_element = vaga_li.locator("a.link--block")
                    
                    titulo = titulo_vaga_element.inner_text().strip()
                    url_vaga = link_vaga_element.get_attribute('href')
                    
                    dados_vaga = {
                        "empresa": "Bosch",
                        "titulo": titulo,
                        "localizacao": "Campinas",
                        "modelo_trabalho": "Hibrido",
                        "url_vaga": url_vaga,
                    }
                    vagas_encontradas.append(dados_vaga)
                    print(f"  - Vaga coletada: {titulo}")

        except TimeoutError:
            print(f"❌ Timeout ao tentar carregar a página: {url}")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado no scraper da Bosch: {e}")
        finally:
            browser.close()
            print("Scraper da Bosch finalizado.")

    return vagas_encontradas

# --- BLOCO DE TESTE COMPLETO COM BANCO DE DADOS DEDICADO ---
if __name__ == "__main__":
    # Importa o módulo de banco de dados
    from src.database import database
    import os

    os.makedirs("src/database", exist_ok=True) 
    # Define o nome do banco de dados de teste
    TEST_DB_FILE = "src/database/vagasteste.db"
    
    # Monkey Patch: Altera a variável DB_FILE do módulo database APENAS para esta execução
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA BOSCH EM MODO DE TESTE COMPLETO ---")
    print(f"--- Os resultados serão salvos em '{TEST_DB_FILE}' ---")
    
    # 1. Inicializa o banco de dados de teste
    database.inicializar_banco()
    
    # 2. Executa o scraper para coletar as vagas
    vagas_coletadas = raspar()
    
    # 3. Processa e salva as vagas no banco de teste
    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Bosch encontradas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            # A função salvar_vaga agora usará o TEST_DB_FILE
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo do Teste Bosch: {novas_vagas_salvas} novas vagas foram salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Bosch foi encontrada no teste.")