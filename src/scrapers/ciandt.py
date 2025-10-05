from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import re
import os
from datetime import datetime
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

def salvar_vagas_descartadas(vagas_descartadas, nome_empresa="CI&T"):
    """Salva apenas as vagas que foram descartadas para verificação do filtro."""
    try:
        if not vagas_descartadas:
            print("✅ Nenhuma vaga foi descartada - filtro funcionando perfeitamente!")
            return None
            
        # Criar diretório data se não existir
        os.makedirs("data", exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"data/vagas_descartadas_{nome_empresa.lower().replace('&', 'e')}_{timestamp}.txt"
        
        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
            arquivo.write(f"=== VAGAS DESCARTADAS - {nome_empresa} ===\n")
            arquivo.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            arquivo.write(f"Total de vagas descartadas: {len(vagas_descartadas)}\n")
            arquivo.write(f"Motivo: Localização não está em {LOCAIS_ALVO}\n")
            arquivo.write("="*60 + "\n\n")
            
            for i, vaga in enumerate(vagas_descartadas, 1):
                arquivo.write(f"VAGA DESCARTADA {i:03d}:\n")
                arquivo.write(f"  Texto Original: {vaga['texto_original']}\n")
                arquivo.write(f"  Título Extraído: {vaga['titulo']}\n")
                arquivo.write(f"  Localização Extraída: {vaga['localizacao']}\n")
                arquivo.write(f"  Motivo Descarte: {vaga['motivo']}\n")
                arquivo.write(f"  URL: {vaga['url_vaga']}\n")
                arquivo.write("-" * 40 + "\n\n")
        
        print(f"⚠️ {len(vagas_descartadas)} vagas foram descartadas - verifique o arquivo: {nome_arquivo}")
        return nome_arquivo
        
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo de vagas descartadas: {e}")
        return None

def extrair_titulo_e_localizacao(texto_completo):
    """
    Função inteligente para separar o título da localização.
    Trata casos especiais como minorias e vírgulas no título.
    """
    import re
    
    # Remove quebras de linha e espaços extras
    texto_completo = ' '.join(texto_completo.split())
    
    # Padrões para remover informações sobre vagas afirmativas
    padroes_afirmativos = [
        r'\s*\(.*?afirmativ.*?\)',
        r'\s*\(.*?mulher.*?\)',
        r'\s*\(.*?pessoa.*?deficiência.*?\)',
        r'\s*\(.*?pretas.*?\)',
        r'\s*\(.*?lgbtqiapn.*?\)',
        r'\s*\(.*?diversidade.*?\)',
        r'\s*\(.*?inclus.*?\)',
        r'\s*\|\s*vaga\s+afirmativa.*?(?=\s|$)',
        r'\s*-\s*afirmativa.*?(?=\s|$)',
        r'\s*\|\s*affirmative.*?(?=\s|$)',
        r'\s*exclusiva\s+pcd\s*-?\s*',
    ]
    
    # Remove padrões afirmativos do texto original
    texto_limpo = texto_completo
    for padrao in padroes_afirmativos:
        texto_limpo = re.sub(padrao, '', texto_limpo, flags=re.IGNORECASE)
    
    # Limpa espaços extras após remoção
    texto_limpo = ' '.join(texto_limpo.split())
    
    # Procura por localizações conhecidas
    for local in LOCAIS_ALVO:
        # Cria padrões mais específicos para encontrar a localização
        padroes_local = [
            rf'\b{re.escape(local)}\b\s*$',  # Local no final
            rf'\s+{re.escape(local)}\b\s*$',  # Local no final com espaço
            rf',\s*{re.escape(local)}\b\s*$',  # Local após vírgula no final
        ]
        
        for padrao in padroes_local:
            match = re.search(padrao, texto_limpo, re.IGNORECASE)
            if match:
                # Extrai o título (tudo antes da localização)
                titulo = texto_limpo[:match.start()].strip()
                
                # Remove vírgulas, hífens ou pipes no final do título
                while titulo.endswith((',', '-', '|')):
                    titulo = titulo[:-1].strip()
                
                return titulo, local
    
    # Se não encontrou localização conhecida, tenta o padrão de vírgula
    if ',' in texto_limpo:
        # Pega a última vírgula (mais provável de separar título de localização)
        partes = texto_limpo.rsplit(',', 1)
        if len(partes) == 2:
            titulo_candidato = partes[0].strip()
            localizacao_candidata = partes[1].strip()
            
            # Verifica se a localização candidata é razoável
            # (não muito longa e não contém caracteres especiais típicos de título)
            if (len(localizacao_candidata.split()) <= 3 and 
                len(localizacao_candidata) <= 50 and
                not re.search(r'[()[\]{}]', localizacao_candidata)):
                
                return titulo_candidato, localizacao_candidata
    
    # Se ainda não encontrou, verifica se há alguma localização no meio do texto
    for local in LOCAIS_ALVO:
        if local.lower() in texto_limpo.lower():
            # Encontra a posição e tenta extrair
            match = re.search(rf'\b{re.escape(local)}\b', texto_limpo, re.IGNORECASE)
            if match:
                titulo = texto_limpo[:match.start()].strip()
                while titulo.endswith((',', '-', '|')):
                    titulo = titulo[:-1].strip()
                return titulo, local
            
    return texto_completo, "Local não especificado"

# --- FUNÇÃO PRINCIPAL DO SCRAPER ---
def raspar():
    print("🚀 Iniciando scraping da CI&T...")
    vagas_encontradas = []
    vagas_descartadas = []


    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=False)
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
                    link_relativo = item.locator('a').get_attribute('href')
                    url_vaga = f"{BASE_URL}{link_relativo}"
                    
                    # PASSO 1: CORREÇÃO PRINCIPAL MANTIDA
                    titulo, localizacao = extrair_titulo_e_localizacao(texto_completo_vaga)

                    # Verificar se a localização está nos locais alvo
                    if localizacao not in LOCAIS_ALVO:
                        # Salvar vaga descartada para análise
                        vaga_descartada = {
                            "texto_original": texto_completo_vaga,
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "motivo": f"Localização '{localizacao}' não está em {LOCAIS_ALVO}",
                            "url_vaga": url_vaga
                        }
                        vagas_descartadas.append(vaga_descartada)
                        continue

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
            
            print(f"Scraping da CI&T finalizado.")
            print(f"📊 Vagas válidas para a região: {len(vagas_encontradas)}")
            print(f"🚫 Vagas descartadas: {len(vagas_descartadas)}")

        except TimeoutError as e:
            print(f"❌ Erro de Timeout: A página demorou muito para carregar ou um elemento não foi encontrado. {e}")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado durante o scraping: {e}")
        finally:
            if browser and browser.is_connected():
                browser.close()
    
    # Salvar arquivo TXT das vagas descartadas para verificação
    salvar_vagas_descartadas(vagas_descartadas, "CI&T")
    
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