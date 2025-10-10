# Configurações do projeto 019Jobs em Campinas

# Configurações do banco de dados
DATABASE_CONFIG = {
    "db_file": "database/vagas.db",
    "backup_dir": "database/backups/"
}

# Configurações dos scrapers
SCRAPER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/118.0.0.0 Chrome/118.0.0.0 Safari/537.36",
    "timeout": 60000,
    "headless": False,
    "delay_min": 0.5,
    "delay_max": 1.5
}


# URLs das empresas
EMPRESA_URLS = {
    "Bosch": "https://careers.smartrecruiters.com/BoschGroup/brazil",
    "CPFL": "https://vagas.cpfl.com.br/search"
}

# Lista de scrapers ativos
SCRAPERS_ATIVOS = [
    ("Bosch", "Bosch"),
    ("CPFL", "CPFL")
]
