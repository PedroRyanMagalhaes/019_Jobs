# Configurações do projeto Jobs em Campinas

# Configurações do banco de dados
DATABASE_CONFIG = {
    "db_file": "data/vagas.db",
    "backup_dir": "data/backups/"
}

# Configurações dos scrapers
SCRAPER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/118.0.0.0 Chrome/118.0.0.0 Safari/537.36",
    "timeout": 60000,
    "headless": True,
    "delay_min": 0.5,
    "delay_max": 1.5
}

# Localizações alvo para as vagas (apenas Campinas e Brazil)
LOCAIS_ALVO = ["Campinas", "Brazil", "Brasil"]

# URLs das empresas
EMPRESA_URLS = {
    "ciandt": "https://ciandt.com/br/pt-br/carreiras/oportunidades"
}

# Lista de scrapers ativos
SCRAPERS_ATIVOS = [
    ("ciandt", "CI&T")
]
