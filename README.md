# Jobs em Campinas

Sistema automatizado para coleta de vagas de emprego em Campinas e região.

## Estrutura do Projeto

```
├── src/                    # Código fonte principal
│   ├── database/           # Módulos relacionados ao banco de dados
│   │   ├── __init__.py
│   │   └── database.py     # Funções de conexão e manipulação do SQLite
│   ├── scrapers/           # Módulos de web scraping
│   │   ├── __init__.py
│   │   └── ciandt.py       # Scraper para vagas da CI&T
│   └── __init__.py
├── config/                 # Configurações do projeto
│   ├── __init__.py
│   └── settings.py         # Configurações centralizadas
├── data/                   # Dados do projeto
│   ├── Empresas.txt        # Lista de empresas e informações
│   └── vagas.db           # Banco de dados SQLite (gerado automaticamente)
├── docs/                   # Documentação
│   └── Verificação de Empresas em Campinas e Região.pdf
├── app.py                  # Arquivo principal de execução
└── requirements.txt        # Dependências do projeto
```

## Como usar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o scraper:
   ```bash
   python app.py
   ```

## Configurações

As configurações do projeto estão centralizadas em `config/settings.py`, incluindo:
- URLs das empresas
- Configurações do banco de dados
- Configurações dos scrapers
- Localizações alvo

## Adicionando novos scrapers

1. Crie um novo arquivo em `src/scrapers/`
2. Implemente a função `raspar()` que retorna uma lista de vagas
3. Adicione o scraper em `config/settings.py` na lista `SCRAPERS_ATIVOS`
4. Atualize o mapeamento em `app.py` se necessário
