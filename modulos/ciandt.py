from playwright.sync_api import sync_playwright, TimeoutError
import time
import random

# Definir constantes no início do arquivo torna o código mais legível e fácil de manter.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
URL_CIANDT = "https://ciandt.com/br/pt-br/carreiras/oportunidades"
BASE_URL = "https://ciandt.com"

def human_delay(min_seconds=0.5, max_seconds=2):

    time.sleep(random.uniform(min_seconds, max_seconds))

def raspar_ciandt():
    print("🚀 Iniciando scraping da CI&T...")
    vagas_encontradas = []

    with sync_playwright() as p:
        browser = None # Inicializa a variável do navegador
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=USER_AGENT,
                locale='pt-BR'
            )
            page = context.new_page()
            
            print(f"Navegando para a página de carreiras da CI&T...")
            page.goto(URL_CIANDT, timeout=60000)
        
            # Bloco 'try' para lidar com o banner de cookies, que pode ou não aparecer.
            try:
                print("Procurando por banner de cookies para declinar...")
                # Usando o XPath fornecido para localizar o botão 'Declinar'.
                decline_button = page.locator('xpath=/html/body/div[2]/div/div/div[2]/button[2]')
                decline_button.click(timeout=5000)
                print("✅ Banner de cookies declinado com sucesso.")
                human_delay()
            except TimeoutError:
                print("☑️ Banner de cookies não encontrado ou não visível (o que é normal).")

            try:
                print("Fechando botao OK")
                ok_button = page.locator('xpath=//*[@id="modalOkBtn"]')
                ok_button.click(timeout=5000)
                print("✅ Botao OK fechado com sucesso.")
            except TimeoutError:
                print("☑️ Botao OK não encontrado ou não visível (o que é normal).")

            
            # --- Interação com a página para filtrar vagas ---
            print("Filtrando por vagas no Brasil...")
            searcth_input = page.locator('#filter-by-text')
            searcth_input.fill("Brazil")
            searcth_input.press("Enter")

            print("Buscando a lista de vagas...")
            vagas_items = page.locator('div.opprtunity-item').all()
            print(f"Encontrados {len(vagas_items)} itens de vagas na página.")

            if not vagas_items:
                print("Nenhuma vaga encontrada após aplicar o filtro.")
                return []

            # Itera sobre cada item de vaga encontrado para extrair as informações.
            for item in vagas_items:
                try:
                    titulo = item.locator('h2').inner_text()
                    partes_titulo = titulo.split(',')
                    link_relativo = item.locator('a').get_attribute('href')

                    url_vaga = f"{BASE_URL}{link_relativo}"
                    
                    localizacao = ", ".join([p.strip() for p in partes_titulo[1:]]) if len(partes_titulo) > 1 else "Brazil"
                    if "Brazil" not in localizacao and "Campinas" not in localizacao:
                        continue
  
                    titulo_limpo = titulo.split(',')[0].strip()

                    modelo_trabalho = "Nao informado"
                    hidden_span_text = item.locator('span.sr-only.filters-item').inner_text()

                    modelo_palavra_chave = hidden_span_text.split()
                    for palavra in modelo_palavra_chave:
                        if palavra.startswith('Workplace_type_'):
                            modelo_trabalho = palavra.split('_')[-1]
                            break

                    vaga = {
                        "empresa": "CI&T",
                        "titulo": titulo_limpo,
                        "modelo_trabalho": modelo_trabalho,
                        "localizacao": localizacao,
                        "url_vaga": url_vaga,
                    }
                    vagas_encontradas.append(vaga)
                except Exception as e:
                    print(f"⚠️ Erro ao extrair dados de um item de vaga: {e}")
            
            print(f"Scraping da CI&T finalizado. Total de vagas extraídas: {len(vagas_encontradas)}")

        except TimeoutError as e:
            print(f"❌ Erro de Timeout: A página demorou muito para carregar ou um elemento não foi encontrado. {e}")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado durante o scraping: {e}")
        finally:
            if browser and browser.is_connected():
                browser.close()
    
    return vagas_encontradas


if __name__ == "__main__":
    print("--- MODO DE TESTE DO SCRAPER CI&T ---")
    vagas_coletadas = raspar_ciandt()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! Total de {len(vagas_coletadas)} vagas encontradas.")
        print("--- Exibindo as 5 primeiras vagas: ---")

        for i, vaga in enumerate(vagas_coletadas): # Limita a exibição às 5 primeiras
            print(f"\n--- VAGA {i+1} ---")
            print(vaga)
    else:
        print("\n❌ Nenhuma vaga foi encontrada durante o teste.")
