from src.database import database
from src.scrapers import ciandt
from config.settings import SCRAPERS_ATIVOS

# Mapeamento de nomes para módulos
SCRAPERS_MAP = {
    "ciandt": ciandt
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

    print("\n==============================================")
    print("== PROCESSO FINALIZADO ==")
    print("📄 Verifique a pasta 'data/' para arquivos de vagas descartadas!")


if __name__ == "__main__":
    main()