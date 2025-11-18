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
from config.settings import SCRAPERS_ATIVOS

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
    "Ifood": Ifood
}

# Criar lista de scrapers a partir das configurações
SCRAPERS_A_EXECUTAR = [
    (SCRAPERS_MAP[nome_modulo], nome_empresa) 
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

    for scraper_module, nome_empresa in SCRAPERS_A_EXECUTAR:
        print(f"\n--- PASSO: Executando Scraper da {nome_empresa} ---")
        vagas_coletadas = []
        try:
            # Padronização: todo módulo de scraper deve ter uma função chamada 'raspar()'
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
            print(f"Nenhuma vaga nova da {nome_empresa} para salvar.")

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

    # Passo extra: Processar Funil Inteligente e salvar em vagas_filtradas.db
    print("\n--- PASSO EXTRA: Processando Funil Inteligente ---")
    try:
        from src.database.processa_funil import processar_funil
        processar_funil()
        print("Funil Inteligente executado com sucesso. Resultados salvos em vagas_filtradas.db.")
    except Exception as e:
        print(f"❌ Erro ao executar o Funil Inteligente: {e}")
    
if __name__ == "__main__":
    main()