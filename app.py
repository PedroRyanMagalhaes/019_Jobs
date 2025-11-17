from src.database import database
from src.database import database_tech 
from src.IA.classificador import ClassificadorVagasTech
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
    database_tech.inicializar_banco_tech()

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
        else:
            print(f"Nenhuma vaga nova da {nome_empresa} para salvar.")

    print("\n--- PASSO FINAL: Classificando Vagas Tech com IA ---")
    classificador = ClassificadorVagasTech()
    vagas_tech_encontradas = classificador.processar_vagas_novas()
    
    # Estatísticas finais
    total_tech = database_tech.contar_vagas_tech()
    vagas_por_empresa = database_tech.listar_vagas_tech_por_empresa()

    print(f"\n📊 RESUMO FINAL:")
    print(f"   • Vagas tech processadas agora: {vagas_tech_encontradas}")
    print(f"   • Total vagas tech no banco: {total_tech}")
    print(f"   • Banco principal: {database.DB_FILE}")
    print(f"   • Banco tech: {database_tech.DB_TECH_FILE}")
    
    if vagas_por_empresa:
        print(f"\n📈 TOP EMPRESAS TECH:")
        for empresa, count in list(vagas_por_empresa.items())[:5]:
            print(f"   • {empresa}: {count} vagas")

    print("\n==============================================")
    print("== PROCESSO FINALIZADO ==")
    
if __name__ == "__main__":
    main()