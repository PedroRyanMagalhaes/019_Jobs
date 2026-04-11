# Ajusta o path quando executado diretamente
if __name__ == "__main__":
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))

import time
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
from config.settings import EMPRESA_URLS, SCRAPER_CONFIG
import os

def raspar():
    """
    Realiza o scraping das vagas da Kumulus (Plataforma Quickin).
    - Carrega a tabela de vagas.
    - Extrai dados com BeautifulSoup.
    - Filtra por Campinas.
    """
    
    url = EMPRESA_URLS.get("Kumulus")
    if not url:
        print("❌ URL da Kumulus não encontrada nas configurações.")
        return []

    vagas_para_salvar = []

    print(f"Iniciando scraper para a Kumulus em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        html_content = ""
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # Espera a tabela aparecer
            try:
                page.wait_for_selector('table.table', timeout=15000)
            except:
                print("Tabela de vagas não encontrada.")
                return []

            # Scroll suave para garantir que todas as linhas renderizem
            print("Rolando a página para carregar todas as linhas...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # Extrai o HTML da tabela
            html_content = page.locator('table.table tbody').inner_html()
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Kumulus: {e}")
        finally:
            if browser.is_connected():
                browser.close()
            print("Fase de captura do Playwright finalizada.")

    if not html_content:
        return []

    print("\nIniciando parse com BeautifulSoup...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Cada vaga é uma linha <tr>
    linhas = soup.find_all('tr')
    print(f"Encontrados {len(linhas)} linhas na tabela.")

    for tr in linhas:
        # Título e Link estão no <th>
        th = tr.find('th')
        link_tag = th.find('a') if th else None
        
        # Localização e Modelo estão no <td>
        td = tr.find('td')
        spans = td.find_all('span') if td else []

        if not link_tag or len(spans) < 2:
            continue

        titulo = link_tag.get_text(strip=True)
        url_vaga = link_tag.get('href')
        
        # O primeiro span é a cidade (ex: Campinas)
        localizacao = spans[0].get_text(strip=True)
        
        # O segundo span (com classe badge) é o modelo (ex: Remoto)
        modelo_texto = spans[1].get_text(strip=True)

        # Filtro de Localização (Campinas)
        if 'campinas' in localizacao.lower():
            
            # Ajuste do Modelo para o nosso padrão
            modelo = "Presencial"
            if 'remoto' in modelo_texto.lower():
                modelo = "Remoto"
            elif 'híbrido' in modelo_texto.lower() or 'hybrid' in modelo_texto.lower():
                modelo = "Híbrido"

            dados_vaga = {
                "empresa": "Kumulus",
                "titulo": titulo,
                "localizacao": localizacao,
                "modelo_trabalho": modelo,
                "url_vaga": url_vaga
            }
            vagas_para_salvar.append(dados_vaga)
            print(f"  [VAGA VÁLIDA] {titulo} ({localizacao}) -> {modelo}")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    import os
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DA KUMULUS EM MODO DE TESTE ---")
    
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Kumulus'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da Kumulus selecionadas.")
        for vaga in vagas_coletadas:
            database.salvar_vaga(vaga)
        print(f"\nResumo: {len(vagas_coletadas)} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga da Kumulus foi selecionada no teste.")