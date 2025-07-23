from playwright.sync_api import sync_playwright, TimeoutError
import time
import random

# User agent para simular um navegador comum e evitar bloqueios simples
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
URL_CIANDT = "https://ciandt.com/br/pt-br/carreiras/oportunidades"
BASE_URL = "https://ciandt.com"

def human_delay(min_seconds=2, max_seconds=5):
    """Simula um atraso humano para não sobrecarregar o servidor."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def raspar_ciandt():
    """
    Realiza o web scraping das vagas da CI&T no Brasil.
    Utiliza técnicas para parecer mais 'humano'.
    """
    print("🚀 Iniciando scraping da CI&T...")
    vagas_encontradas = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True) # Mude para False para ver o navegador em ação
            
            # Cria um contexto de navegador com configurações que mascaram a automação
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR'
            )
            page = context.new_page()
            
            print(f"Navegando para {URL_CIANDT}...")
            page.goto(URL_CIANDT, timeout=60000)
            
            # Espera a página carregar completamente e adiciona um delay
            page.wait_for_load_state('networkidle')
            human_delay()

            # Tenta aceitar o banner de cookies se ele aparecer
            try:
                print("Procurando por banner de cookies...")
                cookie_button = page.locator('button:has-text("Aceitar e fechar")')
                if cookie_button.is_visible():
                    cookie_button.click()
                    print("Banner de cookies aceito.")
                    human_delay()
            except TimeoutError:
                print("Banner de cookies não encontrado ou não visível.")

            # Filtra por vagas no Brasil
            print("Filtrando por vagas no Brasil...")
            page.locator('button:has-text("País")').click()
            human_delay(1, 2)
            page.locator('label:has-text("Brazil")').click()
            
            # Espera o filtro ser aplicado
            print("Aguardando aplicação do filtro...")
            page.wait_for_timeout(5000) # Espera explícita para a UI atualizar

            print("Buscando a lista de vagas...")
            # Localiza todos os contêineres de vagas
            vagas_items = page.locator('div.opprtunity-item').all()
            print(f"Encontrados {len(vagas_items)} itens de vagas na página.")

            if not vagas_items:
                print("Nenhuma vaga encontrada após aplicar o filtro.")
                return []

            for item in vagas_items:
                try:
                    titulo = item.locator('h2').inner_text()
                    link_relativo = item.locator('a').get_attribute('href')
                    url_vaga = f"{BASE_URL}{link_relativo}"
                    
                    # Limpa o título, removendo a localidade que vem junto
                    titulo_limpo = titulo.split(',')[0].strip()
                    
                    vaga = {
                        "empresa": "CI&T",
                        "titulo": titulo_limpo,
                        "localizacao": "Brazil",
                        "url_vaga": url_vaga,
                    }
                    vagas_encontradas.append(vaga)
                except Exception as e:
                    print(f"Erro ao extrair dados de um item de vaga: {e}")
            
            print(f"Scraping da CI&T finalizado. Total de vagas extraídas: {len(vagas_encontradas)}")

        except TimeoutError as e:
            print(f"❌ Erro de Timeout: A página demorou muito para carregar ou um elemento não foi encontrado. {e}")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado durante o scraping: {e}")
        finally:
            if 'browser' in locals() and browser.is_connected():
                browser.close()
    
    return vagas_encontradas

