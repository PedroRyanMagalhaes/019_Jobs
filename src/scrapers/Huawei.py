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
    Realiza o scraping completo das vagas da Huawei.
    - Carrega a página
    - Extrai vagas do Brasil
    - Filtra por vagas de Campinas e Sorocaba
    """
    
    url = EMPRESA_URLS.get("Huawei")
    if not url:
        print("❌ URL da Huawei não encontrada nas configurações.")
        return []

    vagas_para_salvar = []
    base_url = "https://career.huawei.com/reccampportal/la/"

    print(f"Iniciando scraper para a Huawei em {url}")

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

            # --- ETAPA 1: ACEITAR COOKIES ---
            print("Procurando por banner de cookies...")
            try:
                cookie_button = page.locator('a.btn-accept')
                cookie_button.wait_for(state="visible", timeout=10000)
                cookie_button.click()
                print("✅ Banner de cookies aceito.")
                
                print("Aguardando página recarregar após o aceite dos cookies...")
                page.wait_for_load_state("networkidle", timeout=15000)
                print("✅ Página recarregada.")
            except Exception as e:
                print(f"⚠️ Banner de cookies não encontrado ou já aceito: {e}")

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
            with open("huawei_debug.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("HTML salvo em huawei_debug.html")
            
            # Estrutura HTML da Huawei:
            # <div class="public-table">
            #   <ul>
            #     <li class="border-top">
            #       <a href="portal5/social-recruitment-detail.html?jobId=...">
            #         <div class="td"><h6>Título</h6></div>
            #         <div class="th"><p>Brazil/City</p></div>
            #         ...
            
            # Encontra a tabela de vagas
            tabela_vagas = soup.find('div', class_='public-table')
            
            if not tabela_vagas:
                print("⚠️ Tabela de vagas não encontrada.")
                print("Procurando por elementos alternativos...")
                
                # Tenta encontrar todos os links com vagas
                all_links = soup.find_all('a', href=True)
                print(f"Total de links encontrados: {len(all_links)}")
                
                # Filtra links que parecem ser de vagas
                job_links = [link for link in all_links if 'jobId' in link.get('href', '')]
                print(f"Links de vagas (com jobId): {len(job_links)}")
                
                if job_links:
                    print("\nProcessando vagas encontradas por links diretos...")
                    vagas_items = job_links
                    # Processa os links diretos
                    for link_tag in vagas_items:
                        try:
                            # Encontra h6 dentro do link
                            titulo_tag = link_tag.find('h6')
                            if not titulo_tag:
                                continue
                            
                            titulo = titulo_tag.get_text(strip=True)
                            
                            # Encontra todos os <p> dentro do link
                            p_tags = link_tag.find_all('p')
                            if not p_tags or len(p_tags) < 1:
                                continue
                            
                            localizacao = p_tags[0].get_text(strip=True)
                            localizacao_lower = localizacao.lower()
                            
                            print(f"  Analisando: {titulo} - {localizacao}")
                            
                            # Filtra apenas Campinas e Sorocaba
                            cidade_aceita = False
                            if 'campinas' in localizacao_lower:
                                cidade_aceita = True
                            elif 'sorocaba' in localizacao_lower:
                                cidade_aceita = True
                            
                            if not cidade_aceita:
                                print(f"    ❌ Rejeitada (cidade não aceita)")
                                continue
                            
                            # Monta URL completa
                            url_relativa = link_tag['href']
                            if url_relativa.startswith('http'):
                                url_vaga = url_relativa
                            else:
                                url_vaga = f"{base_url}{url_relativa}"
                            
                            # Determina modelo de trabalho
                            modelo = "Não informado"
                            if any(word in localizacao_lower for word in ['remote', 'remoto', 'home office']):
                                modelo = "Remoto"
                            elif any(word in localizacao_lower for word in ['hybrid', 'híbrido', 'hibrido']):
                                modelo = "Híbrido"
                            else:
                                modelo = "Presencial"
                            
                            dados_vaga = {
                                "empresa": "Huawei",
                                "titulo": titulo,
                                "localizacao": localizacao,
                                "modelo_trabalho": modelo,
                                "url_vaga": url_vaga
                            }
                            vagas_para_salvar.append(dados_vaga)
                            print(f"    ✅ [VAGA VÁLIDA] {titulo} ({localizacao})")
                            
                        except Exception as e:
                            print(f"    ⚠️ Erro ao processar link: {e}")
                            continue
                else:
                    print("Nenhum link de vaga encontrado. Verifique huawei_debug.html")
                    return []
            else:
                # Encontra todos os li dentro da tabela
                vagas_items = tabela_vagas.find_all('li')
                
                if not vagas_items:
                    print("⚠️ Nenhuma vaga encontrada na tabela.")
                    return []
                
                print(f"Analisando {len(vagas_items)} vagas encontradas.")
                
                for item in vagas_items:
                    try:
                        # Encontra o link da vaga
                        link_tag = item.find('a', href=True)
                        if not link_tag:
                            continue
                        
                        # Título está em <div class="td"><h6>...</h6></div>
                        titulo_div = link_tag.find('div', class_='td')
                        if not titulo_div:
                            continue
                        
                        titulo_tag = titulo_div.find('h6')
                        if not titulo_tag:
                            continue
                        
                        titulo = titulo_tag.get_text(strip=True)
                        
                        # Localização está no primeiro <div class="th"><p>...</p></div>
                        localizacao_divs = link_tag.find_all('div', class_='th')
                        if not localizacao_divs or len(localizacao_divs) < 1:
                            continue
                        
                        localizacao_tag = localizacao_divs[0].find('p')
                        if not localizacao_tag:
                            continue
                        
                        localizacao = localizacao_tag.get_text(strip=True)
                        localizacao_lower = localizacao.lower()
                        
                        print(f"  Analisando: {titulo} - {localizacao}")
                        
                        # Filtra apenas Campinas e Sorocaba
                        cidade_aceita = False
                        if 'campinas' in localizacao_lower:
                            cidade_aceita = True
                        elif 'sorocaba' in localizacao_lower:
                            cidade_aceita = True
                        
                        if not cidade_aceita:
                            print(f"    ❌ Rejeitada (cidade não aceita)")
                            continue
                        
                        # Monta URL completa
                        url_relativa = link_tag['href']
                        if url_relativa.startswith('http'):
                            url_vaga = url_relativa
                        else:
                            url_vaga = f"{base_url}{url_relativa}"
                        
                        # Determina modelo de trabalho
                        modelo = "Não informado"
                        if any(word in localizacao_lower for word in ['remote', 'remoto', 'home office']):
                            modelo = "Remoto"
                        elif any(word in localizacao_lower for word in ['hybrid', 'híbrido', 'hibrido']):
                            modelo = "Híbrido"
                        else:
                            modelo = "Presencial"
                        
                        dados_vaga = {
                            "empresa": "Huawei",
                            "titulo": titulo,
                            "localizacao": localizacao,
                            "modelo_trabalho": modelo,
                            "url_vaga": url_vaga
                        }
                        vagas_para_salvar.append(dados_vaga)
                        print(f"    ✅ [VAGA VÁLIDA] {titulo} ({localizacao})")
                        
                    except Exception as e:
                        print(f"    ⚠️ Erro ao processar item: {e}")
                        continue

        except Exception as e:
            print(f"❌ Ocorreu um erro crítico no scraper da Huawei: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if browser.is_connected():
                browser.close()
            print("Scraper finalizado.")

    print(f"\nAnálise finalizada. {len(vagas_para_salvar)} vagas selecionadas para salvar.")
    return vagas_para_salvar

# --- BLOCO DE TESTE ---

