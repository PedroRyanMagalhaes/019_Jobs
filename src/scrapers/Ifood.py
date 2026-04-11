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
    Realiza o scraping das vagas do Ifood.
    - Faz scroll infinito.
    - Limpa o texto 'Ver vaga'.
    - Filtra estritamente: Campinas, Híbrido, Remoto ou 'Brasil' (exato).
    """
    
    url = EMPRESA_URLS.get("Ifood")
    if not url:
        print("❌ URL do Ifood não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://carreiras.Ifood.com.br"

    print(f"Iniciando scraper para o Ifood em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SCRAPER_CONFIG.get("headless", True))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # --- SCROLL INFINITO ---
            print("Iniciando scroll para carregar todas as vagas...")
            last_height = 0
            no_change_count = 0
            
            for i in range(30): 
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)
                
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3: 
                        print("Fim da página alcançado.")
                        break
                else:
                    no_change_count = 0
                
                last_height = new_height
                print(f"Scroll {i+1}...")

            print("Extraindo HTML final...")
            html_content = page.content()
            
        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper do Ifood: {e}")
            html_content = ""
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    if not html_content:
        return []

    print("\nIniciando parse com BeautifulSoup...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Tenta pegar as vagas pelo seletor de lista
    vagas_li = soup.find_all('li', class_='sc-byTJDB') 
    
    if not vagas_li:
        print("⚠️ Classe específica não encontrada, tentando busca genérica...")
        todos_li = soup.find_all('li')
        vagas_li = [li for li in todos_li if li.find('a', href=True) and '/job/' in li.find('a')['href']]

    print(f"Encontrados {len(vagas_li)} elementos de vagas.")

    for vaga in vagas_li:
        link_tag = vaga.find('a')
        if not link_tag: continue

        # Título
        titulo_tag = vaga.find('h3')
        titulo = titulo_tag.get_text(strip=True) if titulo_tag else link_tag.get('title', 'Título não encontrado')
        
        # Link
        url_relativa = link_tag.get('href', '')
        url_vaga = f"{base_url}{url_relativa}"

        # --- LIMPEZA E EXTRAÇÃO DA LOCALIZAÇÃO ---
        # Pega todos os h5, MAS EXCLUI AQUELE QUE TEM "Ver vaga"
        infos_sujas = [tag.get_text(strip=True) for tag in vaga.find_all('h5')]
        infos_limpas = [texto for texto in infos_sujas if "Ver vaga" not in texto]
        
        # Junta o que sobrou (Geralmente é "Sênior" e "Brasil")
        localizacao_texto = " | ".join(infos_limpas)

        # --- LÓGICA DE FILTRO RIGOROSA ---
        local_lower = localizacao_texto.lower().strip()
        
        modelo = "Não informado"
        salvar = False

        # 1. Verifica palavras-chave fortes primeiro
        if 'híbrido' in local_lower or 'hibrido' in local_lower:
            modelo = "Híbrido"
            salvar = True
        elif 'remoto' in local_lower or 'remote' in local_lower:
            modelo = "Remoto"
            salvar = True
        elif 'campinas' in local_lower:
            # Se for de Campinas, assumimos Híbrido se não disser o contrário
            if modelo == "Não informado": modelo = "Híbrido"
            salvar = True
        
        # 2. Verifica se é ESTRITAMENTE "Brasil" ou "Brazil" (Vaga Nacional/Remota)
        # Isso evita pegar "Osasco, Brasil" ou "Limeira, Brasil"
        elif local_lower == 'brasil' or local_lower == 'brazil':
             modelo = "Remoto"
             salvar = True

        if salvar:
            dados_vaga = {
                "empresa": "Ifood",
                "titulo": titulo,
                "localizacao": localizacao_texto, 
                "modelo_trabalho": modelo,
                "url_vaga": url_vaga
            }
            vagas_para_salvar.append(dados_vaga)
            print(f"  [VAGA VÁLIDA] {titulo} ({localizacao_texto}) -> {modelo}")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    from src.database import database
    import os
    
    os.makedirs("src/database", exist_ok=True)
    TEST_DB_FILE = "src/database/vagasteste.db"
    database.DB_FILE = TEST_DB_FILE
    
    print(f"--- EXECUTANDO SCRAPER DO Ifood EM MODO DE TESTE ---")
    
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'Ifood'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas do Ifood selecionadas.")
        for vaga in vagas_coletadas:
            database.salvar_vaga(vaga)
        print(f"\nResumo: {len(vagas_coletadas)} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n❌ Nenhuma vaga do Ifood foi selecionada no teste.")