from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import re
from config.settings import SCRAPER_CONFIG, LOCAIS_ALVO, EMPRESA_URLS

# --- CONSTANTES ---
USER_AGENT = SCRAPER_CONFIG["user_agent"]
URL_CIANDT = EMPRESA_URLS["ciandt"]
BASE_URL = "https://ciandt.com"

# --- FUNÇÕES AUXILIARES ---
def human_delay(min_seconds=None, max_seconds=None):
    """Pausa a execução por um tempo aleatório para simular comportamento humano."""
    min_sec = min_seconds or SCRAPER_CONFIG["delay_min"]
    max_sec = max_seconds or SCRAPER_CONFIG["delay_max"]
    time.sleep(random.uniform(min_sec, max_sec))

def extrair_titulo_e_localizacao(texto_completo):
    """
    Função inteligente para separar o título da localização.
    Busca pelas palavras-chave de localização (LOCAIS_ALVO) de trás para frente.
    """
    texto_lower = texto_completo.lower()
    
    for local in LOCAIS_ALVO:
        posicao = texto_lower.rfind(local.lower())
        
        if posicao != -1:
            titulo = texto_completo[:posicao].strip()
            if titulo.endswith(',') or titulo.endswith('-'):
                titulo = titulo[:-1].strip()
            
            localizacao = texto_completo[posicao:].strip()
            return titulo, localizacao
            
    return texto_completo, "Local não especificado"

# --- FUNÇÃO PRINCIPAL DO SCRAPER ---
def raspar():
    print("🚀 Iniciando scraping da CI&T...")
    vagas_encontradas = []

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT, locale='pt-BR')
            page = context.new_page()
            
            print("Navegando para a página de carreiras da CI&T...")
            page.goto(URL_CIANDT, timeout=60000)
        
            # SELETORES MANTIDOS COMO O ORIGINAL
            try:
                print("Procurando por banner de cookies para declinar...")
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
            
            print("Filtrando por vagas no Brasil...")
            # CORREÇÃO DE TYPO MANTIDA
            search_input = page.locator('#filter-by-text')
            search_input.fill("Brazil")
            search_input.press("Enter")
            page.wait_for_timeout(3000) 

            print("Buscando a lista de vagas...")
            # CORREÇÃO DE TYPO MANTIDA
            vagas_items = page.locator('div.opprtunity-item').all()
            print(f"Encontrados {len(vagas_items)} itens de vagas na página.")

            if not vagas_items:
                print("Nenhuma vaga encontrada após aplicar o filtro.")
                return []

            for item in vagas_items:
                try:
                    texto_completo_vaga = item.locator('h2').inner_text()
                    
                    # PASSO 1: CORREÇÃO PRINCIPAL MANTIDA
                    titulo, localizacao = extrair_titulo_e_localizacao(texto_completo_vaga)

                    if localizacao == "Local não especificado":
                        continue

                    link_relativo = item.locator('a').get_attribute('href')
                    url_vaga = f"{BASE_URL}{link_relativo}"
                    
                    # PASSO 4: REFATORAÇÃO DO MODELO DE TRABALHO MANTIDA
                    modelo_trabalho = "Nao informado"
                    try:
                        hidden_span_text = item.locator('span.sr-only.filters-item').inner_text(timeout=1000)
                        match = re.search(r'Workplace_type_(\w+)', hidden_span_text)
                        if match:
                            modelo_trabalho = match.group(1).replace("Remote", "Remoto")
                    except (TimeoutError, AttributeError):
                        pass

                    vaga = {
                        "empresa": "CI&T",
                        "titulo": titulo,
                        "modelo_trabalho": modelo_trabalho,
                        "localizacao": localizacao,
                        "url_vaga": url_vaga,
                    }
                    vagas_encontradas.append(vaga)
                except Exception as e:
                    print(f"⚠️ Erro ao extrair dados de um item de vaga: {e}")
            
            print(f"Scraping da CI&T finalizado. Total de vagas válidas para a região: {len(vagas_encontradas)}")

        except TimeoutError as e:
            print(f"❌ Erro de Timeout: A página demorou muito para carregar ou um elemento não foi encontrado. {e}")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado durante o scraping: {e}")
        finally:
            if browser and browser.is_connected():
                browser.close()
    
    return vagas_encontradas

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    print("--- MODO DE TESTE DO SCRAPER CI&T ---")
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! Total de {len(vagas_coletadas)} vagas encontradas.")
        print("--- Exibindo as 5 primeiras vagas: ---")

        for i, vaga in enumerate(vagas_coletadas[:5]):
            print(f"\n--- VAGA {i+1} ---")
            print(vaga)
    else:
        print("\n❌ Nenhuma vaga foi encontrada durante o teste.")