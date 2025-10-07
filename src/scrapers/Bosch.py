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
            # --- CORREÇÃO APLICADA AQUI ---
            # Adicionada a classe .openings-section para especificar o seletor
            campinas_section = page.locator("section.openings-section:has(h3:has-text('Campinas, Brasil'))")
            
            if not campinas_section.is_visible():
                print("⚠️ Seção de Campinas não encontrada na página. Encerrando scraper da Bosch.")
                browser.close()
                return []
            
            print("✅ Seção de Campinas encontrada.")

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
                    print("Todas as vagas de Campinas foram carregadas.")
                    break

            print("Coletando informações das vagas...")
            lista_vagas_li = campinas_section.locator("li.opening-job")
            count = lista_vagas_li.count()
            print(f"Encontrados {count} elementos de vagas.")

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