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
    Realiza o scraping completo das vagas da General Motors.
    - Carrega a página
    - Extrai vagas do Brasil
    - Filtra por vagas de Campinas e Sorocaba
    """
    
    url = EMPRESA_URLS.get("Generalmotors")
    if not url:
        print("❌ URL da General Motors não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://search-careers.gm.com"

    print(f"Iniciando scraper para a General Motors em {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=SCRAPER_CONFIG.get("headless", True)
        )
        context = browser.new_context(
            user_agent=SCRAPER_CONFIG.get("user_agent")
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG.get("timeout", 60000))
            print("✅ Página carregada.")

            # Aguardar carregamento da lista de vagas
            print("Aguardando lista de vagas carregar...")
            time.sleep(5)  # Espera inicial para renderização
            
            # Scroll para carregar todas as vagas (se houver lazy loading)
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            # Extrai o HTML
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # DEBUG: Salvar HTML para inspeção
            print("Salvando HTML para debug...")
            with open("generalmotors_debug.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("HTML salvo em generalmotors_debug.html")
            
            # Estrutura HTML da General Motors:
            # <div class="card card-job js-animate">
            #   <div class="card-body">
            #     <ul class="list-inline job-meta">
            #       <li class="list-inline-item">
            #         <svg><use xlink:href="/Images/sprite.svg#map-marker"></use></svg>
            #         Sorocaba, São Paulo
            #       </li>
            #     </ul>
            #     <h2 class="card-title">
            #       <a class="stretched-link" href="/pt/cargos/...">Título da vaga</a>
            #     </h2>
            #   </div>
            # </div>
            
            # Encontra todos os cards de vagas
            vagas_items = soup.find_all('div', class_='card-job')
            
            if not vagas_items:
                print("⚠️ Nenhum card de vaga encontrado. Verifique generalmotors_debug.html")
                return []
            
            print(f"Analisando {len(vagas_items)} vagas encontradas.")
            
            for item in vagas_items:
                try:
                    # Título está em <h2 class="card-title"><a>...</a></h2>
                    titulo_tag = item.find('h2', class_='card-title')
                    if not titulo_tag:
                        continue
                    
                    link_tag = titulo_tag.find('a')
                    if not link_tag:
                        continue
                    
                    titulo = link_tag.get_text(strip=True)
                    
                    # Localização está no <li> que contém o ícone map-marker
                    # Procura todos os li dentro de job-meta
                    job_meta = item.find('ul', class_='job-meta')
                    if not job_meta:
                        continue
                    
                    localizacao = "Não informado"
                    localizacao_li = None
                    
                    # Procura o li que contém o svg com map-marker
                    for li in job_meta.find_all('li', class_='list-inline-item'):
                        svg = li.find('svg')
                        if svg:
                            use_tag = svg.find('use')
                            if use_tag and 'map-marker' in use_tag.get('xlink:href', ''):
                                # Encontrou o li com a localização
                                localizacao_li = li
                                # Remove o svg para pegar só o texto
                                svg_copy = svg.extract()
                                localizacao = li.get_text(strip=True)
                                # Recoloca o svg
                                li.insert(0, svg_copy)
                                break
                    
                    if not localizacao or localizacao == "Não informado":
                        continue
                    
                    localizacao_lower = localizacao.lower()
                    
                    print(f"  Analisando: {titulo} - {localizacao}")
                    
                    # Filtra apenas Sorocaba ou Remote/Remoto
                    cidade_aceita = False
                    
                    if 'sorocaba' in localizacao_lower:
                        cidade_aceita = True
                    elif any(word in localizacao_lower for word in ['remote', 'remoto', 'remota']):
                        cidade_aceita = True
                    
                    if not cidade_aceita:
                        print(f"    ❌ Rejeitada (cidade não aceita: {localizacao})")
                        continue
                    
                    # Monta URL completa
                    url_relativa = link_tag.get('href', '')
                    if url_relativa.startswith('http'):
                        url_vaga = url_relativa
                    elif url_relativa.startswith('/'):
                        url_vaga = f"{base_url}{url_relativa}"
                    else:
                        url_vaga = f"{base_url}/{url_relativa}"
                    
                    # Determina modelo de trabalho
                    modelo = "Não informado"
                    if any(word in localizacao_lower for word in ['remote', 'remoto', 'remota']):
                        modelo = "Remoto"
                    elif any(word in localizacao_lower for word in ['hybrid', 'híbrido', 'hibrido']):
                        modelo = "Híbrido"
                    else:
                        modelo = "Presencial"
                    
                    dados_vaga = {
                        "empresa": "General Motors",
                        "titulo": titulo,
                        "localizacao": localizacao,
                        "modelo_trabalho": modelo,
                        "url_vaga": url_vaga
                    }
                    vagas_para_salvar.append(dados_vaga)
                    print(f"    ✅ [VAGA VÁLIDA] {titulo} ({localizacao})")
                    
                except Exception as e:
                    print(f"  ⚠️ Erro ao processar item: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da General Motors: {e}")
            import traceback
            traceback.print_exc()
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
    
    print(f"--- EXECUTANDO SCRAPER DA GENERAL MOTORS EM MODO DE TESTE ---")
    
    database.inicializar_banco()
    conn = database.sqlite3.connect(TEST_DB_FILE)
    conn.execute("DELETE FROM vagas WHERE empresa = 'General Motors'")
    conn.commit()
    conn.close()
    
    vagas_coletadas = raspar()

    if vagas_coletadas:
        print(f"\n✅ SUCESSO! {len(vagas_coletadas)} vagas da General Motors selecionadas.")
        novas_vagas_salvas = 0
        for vaga in vagas_coletadas:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo: {novas_vagas_salvas} novas vagas salvas em '{TEST_DB_FILE}'.")
    else:
        print("\n⚠️ AVISO: Nenhuma vaga de Campinas/Sorocaba encontrada no momento.")
        print("O scraper pode precisar de ajustes nos seletores HTML.")
        print("Verifique o arquivo 'generalmotors_debug.html' gerado para identificar os seletores corretos.")
