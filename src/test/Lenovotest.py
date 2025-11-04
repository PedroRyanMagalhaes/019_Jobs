from playwright.sync_api import sync_playwright
import json
from datetime import datetime

def analisar_site(url, nome_empresa):
    """
    Analisa um site de vagas e extrai toda estrutura HTML útil
    """
    print(f"🔍 Analisando site da {nome_empresa}...")
    print(f"📡 URL: {url}\n")
    
    resultado = {
        "empresa": nome_empresa,
        "url": url,
        "data_analise": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "elementos_encontrados": {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=60000, wait_until="networkidle")
            print("✅ Página carregada com sucesso!\n")
            
            # Espera um pouco para JavaScript carregar
            page.wait_for_timeout(3000)
            
            # Lista de seletores comuns para vagas
            seletores_comuns = [
                # Containers de vagas
                "article", "div[class*='job']", "div[class*='card']", 
                "li[class*='job']", "div[class*='vacancy']", "div[class*='position']",
                "tr[class*='job']", "[data-job-id]", "[data-position]",
                
                # Títulos
                "h1", "h2", "h3", "h4", "[class*='title']", "[class*='heading']",
                
                # Links
                "a[href*='job']", "a[href*='career']", "a[href*='position']",
                
                # Localizações
                "[class*='location']", "[class*='city']", "[class*='address']",
                
                # Descrições
                "[class*='description']", "[class*='summary']", "p",
                
                # Listas
                "ul", "ol", "table"
            ]
            
            print("📋 Buscando elementos relevantes...\n")
            
            for seletor in seletores_comuns:
                elementos = page.query_selector_all(seletor)
                
                if elementos and len(elementos) > 0:
                    print(f"✅ Encontrados {len(elementos)} elementos: {seletor}")
                    
                    # Pega exemplos dos primeiros 3 elementos
                    exemplos = []
                    for i, elem in enumerate(elementos[:3]):
                        try:
                            texto = elem.inner_text().strip()[:100]  # Primeiros 100 chars
                            html = elem.inner_html()[:200]  # Primeiros 200 chars do HTML
                            
                            exemplos.append({
                                "indice": i,
                                "texto_visivel": texto,
                                "html_interno": html,
                                "xpath": f"({seletor})[{i+1}]"
                            })
                        except:
                            continue
                    
                    if exemplos:
                        resultado["elementos_encontrados"][seletor] = {
                            "quantidade": len(elementos),
                            "exemplos": exemplos
                        }
            
            # Salva resultado em arquivo JSON
            nome_arquivo = f"analise_{nome_empresa.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            caminho_arquivo = f"tools/analises/{nome_arquivo}"
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Análise salva em: {caminho_arquivo}")
            print(f"\n📊 Total de tipos de elementos encontrados: {len(resultado['elementos_encontrados'])}")
            
            # Também salva uma versão TXT mais legível
            nome_txt = caminho_arquivo.replace('.json', '.txt')
            with open(nome_txt, 'w', encoding='utf-8') as f:
                f.write(f"ANÁLISE DO SITE DA {nome_empresa.upper()}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Data: {resultado['data_analise']}\n")
                f.write("="*80 + "\n\n")
                
                for seletor, dados in resultado['elementos_encontrados'].items():
                    f.write(f"\n{'='*80}\n")
                    f.write(f"SELETOR: {seletor}\n")
                    f.write(f"QUANTIDADE: {dados['quantidade']}\n")
                    f.write(f"{'-'*80}\n")
                    
                    for exemplo in dados['exemplos']:
                        f.write(f"\n[Exemplo {exemplo['indice'] + 1}]\n")
                        f.write(f"Texto: {exemplo['texto_visivel']}\n")
                        f.write(f"HTML: {exemplo['html_interno']}\n")
                        f.write(f"XPath: {exemplo['xpath']}\n")
                        f.write("-" * 40 + "\n")
            
            print(f"📄 Versão legível salva em: {nome_txt}")
            
            input("\n⏸️  Pressione ENTER para fechar o navegador...")
            
        except Exception as e:
            print(f"❌ Erro durante análise: {e}")
        
        finally:
            browser.close()
    
    return resultado


if __name__ == "__main__":
    # Exemplo de uso
    print("="*80)
    print("🔧 ANALISADOR DE SITES DE VAGAS")
    print("="*80)
    print("\nEste script analisa um site e extrai todos os seletores úteis.")
    print("Depois você pode me enviar o arquivo gerado para eu identificar as vagas!\n")
    
    url = input("Digite a URL do site: ").strip()
    empresa = input("Digite o nome da empresa: ").strip()
    
    print("\n")
    analisar_site(url, empresa)
    
    print("\n✅ Análise concluída!")
    print("📤 Agora você pode me enviar os arquivos .json ou .txt gerados")
    print("   e eu vou identificar onde estão as informações das vagas!")