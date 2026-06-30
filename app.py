from src.database import database
from src.scrapers import Ciandt
from src.scrapers import Bosch
from src.scrapers import Johndeere
from src.scrapers import Cpfl
from src.scrapers import Enforce
from src.scrapers import Dell
from src.scrapers import Lenovo
from src.scrapers import Venturus
from src.scrapers import Ype
from src.scrapers import Kryptus
from src.scrapers import Ambevtech
from src.scrapers import Kumulus
from src.scrapers import Sensedia
from src.scrapers import Ifood
from src.scrapers import Ibm
from src.scrapers import Samsung
from src.scrapers import Motorola
from src.scrapers import Eldorado
from src.scrapers import Huawei
from src.scrapers import Generalmotors
from src.scrapers import Honda
from src.scrapers import Goodyear
from src.scrapers import Toyota
from src.scrapers import Tresm
from src.scrapers import Cnhindustrial
from config.settings import SCRAPERS_ATIVOS, EMPRESA_URLS, ENV


# Mapeamento de nomes para módulos
SCRAPERS_MAP = {
    "Bosch": Bosch,
    "CPFL": Cpfl,
    "CI&T": Ciandt,
    "JohnDeere": Johndeere,
    "Enforce": Enforce,
    "Dell": Dell,
    "Lenovo": Lenovo,
    "Venturus": Venturus,
    "Ype": Ype,
    "Kryptus": Kryptus,
    "Sensedia": Sensedia,
    "Ambevtech": Ambevtech,
    "Kumulus": Kumulus,
    "Ifood": Ifood,
    "Ibm": Ibm,
    "Samsung": Samsung,
    "Motorola": Motorola,
    "Eldorado": Eldorado,
    "Huawei": Huawei,
    "Generalmotors": Generalmotors,
    "Honda": Honda,
    "Goodyear": Goodyear,
    "Toyota": Toyota,
    "Tresm": Tresm,
    "Cnhindustrial": Cnhindustrial
    
}

def _url_empresa(modulo_key: str) -> str:
    """Busca URL em EMPRESA_URLS com fallback case-insensitive."""
    if modulo_key in EMPRESA_URLS:
        return EMPRESA_URLS[modulo_key]
    normalizado = modulo_key.lower().replace("&", "").replace(" ", "")
    for k, url in EMPRESA_URLS.items():
        if k.lower() == normalizado:
            return url
    return ""

# Criar lista de scrapers a partir das configurações: (módulo, nome_display, modulo_key)
SCRAPERS_A_EXECUTAR = [
    (SCRAPERS_MAP[nome_modulo], nome_empresa, nome_modulo)
    for nome_modulo, nome_empresa in SCRAPERS_ATIVOS
]

def main():
    print("== INICIANDO PROCESSO DE COLETA DE VAGAS ==")
    print("==============================================")

    print("\n--- PASSO 1: Preparando o Banco de Dados ---")
    database.inicializar_banco()
    
    print("\n--- PASSO 2: Iniciando Ciclo de Scraping ---")
    database.iniciar_ciclo_scraping()

    total_novas_vagas = 0
    scrapers_vazios = []  # (nome_empresa, url) para alerta

    for scraper_module, nome_empresa, modulo_key in SCRAPERS_A_EXECUTAR:
        print(f"\n--- PASSO: Executando Scraper da {nome_empresa} ---")
        vagas_coletadas = []
        try:
            vagas_coletadas = scraper_module.raspar()
        except Exception as e:
            print(f"❌ Falha crítica ao executar o scraper da {nome_empresa}: {e}")

        if vagas_coletadas:
            print(f"Processando {len(vagas_coletadas)} vagas encontradas na {nome_empresa}...")
            novas_vagas_salvas = 0
            for vaga in vagas_coletadas:
                if database.salvar_vaga(vaga):
                    novas_vagas_salvas += 1
            print(f"\nResumo {nome_empresa}: {novas_vagas_salvas} novas vagas foram salvas.")
            total_novas_vagas += novas_vagas_salvas
        else:
            print(f"⚠️  Nenhuma vaga retornada pela {nome_empresa}.")
            scrapers_vazios.append((nome_empresa, _url_empresa(modulo_key)))

    # Alerta de scrapers vazios
    if scrapers_vazios:
        print(f"\n--- ALERTA: {len(scrapers_vazios)} scraper(s) sem vagas ---")
        try:
            from src.newsletter.enviar_alerta import enviar_alerta_scrapers_vazios
            enviar_alerta_scrapers_vazios(scrapers_vazios)
        except Exception as e:
            print(f"❌ Erro ao enviar alerta: {e}")

    print("\n--- PASSO FINAL: Finalizando Ciclo de Scraping ---")
    database.finalizar_ciclo_scraping()
    
    # Estatísticas finais
    vagas_ativas = database.contar_vagas()
    vagas_removidas = database.contar_vagas_removidas()
    
    print("\n==============================================")
    print("== PROCESSO FINALIZADO ==")
    print(f"📊 ESTATÍSTICAS:")
    print(f"   ✅ Novas vagas adicionadas hoje: {total_novas_vagas}")
    print(f"   📈 Total de vagas ativas: {vagas_ativas}")
    print(f"   📦 Total de vagas removidas (histórico): {vagas_removidas}")
    print("==============================================")

    # Passo extra: Processar Funil Inteligente e salvar em vagas_filtradas
    print("\n--- PASSO EXTRA: Processando Funil Inteligente ---")
    try:
        from src.database.processa_funil import processar_funil
        processar_funil()
        print("✅ Funil Inteligente executado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao executar o Funil Inteligente: {e}")

    # Passo extra: Gerar página estática e publicar no GitHub Pages
    print("\n--- PASSO EXTRA: Gerando Página Estática ---")
    try:
        from src.gerar_pagina import gerar_pagina
        gerar_pagina()
    except Exception as e:
        print(f"❌ Erro ao gerar página estática: {e}")

    # Passo final: Enviar Newsletter
    print("\n--- PASSO FINAL: Enviando Newsletter ---")
    try:
        from src.newsletter.enviar_newsletter import enviar_emails
        modo_dev = (ENV == "dev")
        enviar_emails(dev=modo_dev)
        print("✅ Newsletter enviada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar newsletter: {e}")
    
    print("\n==============================================")
    print("🎉 PROCESSO COMPLETO FINALIZADO COM SUCESSO!")
    print("==============================================")
    
if __name__ == "__main__":
    main()