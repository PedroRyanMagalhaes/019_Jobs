# Configurações do projeto 019Jobs em Campinas
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados
DATABASE_CONFIG = {
    "db_file": "src/database/vagas.db",
    "backup_dir": "src/database/backups/"
}

# Configurações de Banco de Dados
DB_FILE = "src/database/vagas.db"

# Configurações dos scrapers
SCRAPER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/118.0.0.0 Chrome/118.0.0.0 Safari/537.36",
    "timeout": 60000,
    "headless": True,
    "delay_min": 0.5,
    "delay_max": 1.5
}


# URLs das empresasbe
EMPRESA_URLS = {
    "Bosch": "https://careers.smartrecruiters.com/BoschGroup/brazil",
    "Cpfl": "https://vagas.cpfl.com.br/search",
    "Ciandt": "https://ciandt.com/br/pt-br/carreiras/oportunidades",
    "Johndeere": "https://careers.deere.com/careers?start=0&location=Brazil&pid=137479995061&sort_by=timestamp&filter_include_remote=1",
    "Enforce": "https://job-boards.greenhouse.io/enforce",
    "Dell": "https://jobs.dell.com/pt-br/busca-de-vagas/Hortol%C3%A2ndia%2C%20S%C3%A3o%20Paulo/375/4/3469034-3448433-6322273-3461655/-22x85833/-47x22/50/2",
    "Lenovo": "https://jobs.lenovo.com/en_US/careers/SearchJobs/?13036=%5B12016606%5D&13036_format=6621&13037=%5B12019986%5D&13037_format=6622&listFilterMode=1&jobRecordsPerPage=10&",
    "Venturus":"https://venturus.inhire.app/vagas/",
    "Ype": "https://carreirasype.gupy.io/",
    "Kryptus": "https://kryptus.gupy.io/",
    "Sensedia": "https://sensedia.hire.trakstar.com/",
    "Ambevtech": "https://ambevtech.gupy.io/",
    "Kumulus": "https://jobs.quickin.io/kumulus/jobs",
    "Ifood": "https://carreiras.ifood.com.br/jobs/"
}

# Lista de scrapers ativos
SCRAPERS_ATIVOS = [
    ("Bosch", "Bosch"),
    ("CPFL", "CPFL"),
    ("CI&T", "CI&T"),
    ("JohnDeere", "John Deere"),
    ("Enforce", "Enforce"),
    ("Dell", "Dell"),
    ("Lenovo", "Lenovo"),
    ("Venturus", "Venturus"),
    ("Ype", "Ype"),
    ("Kryptus", "Kryptus"),
    ("Sensedia", "Sensedia"),
    ("Ambevtech", "Ambevtech"),
    ("Kumulus", "Kumulus"),
    ("Ifood", "Ifood"),
]

# Configuração da Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "SUA_API_KEY_AQUI")  # Lê do arquivo .env
    