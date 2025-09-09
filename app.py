import database
from modulos import ciandt # Futuramente: from modulos import ciandt, cpfl, ...

# --- ÁREA DE CONFIGURAÇÃO ---
# Para adicionar um novo scraper, importe-o acima e adicione-o a esta lista.
# O formato é: (módulo_do_scraper, "Nome da Empresa para Exibição")
SCRAPERS_A_EXECUTAR = [
    (ciandt, "CI&T"),
    # (cpfl, "CPFL Energia"), # Exemplo de como você adicionaria o próximo
]

def main():
    """
    Função principal que orquestra de forma genérica o processo de scraping e armazenamento.
    """
    print("==============================================")
    print("== INICIANDO PROCESSO DE COLETA DE VAGAS ==")
    print("==============================================")

    print("\n--- PASSO 1: Preparando o Banco de Dados ---")
    database.inicializar_banco()

    # Loop principal que executa cada scraper configurado na lista
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
    print("==============================================")


if __name__ == "__main__":
    main()