# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

**019 Jobs** is a daily job-scraping pipeline targeting tech companies in the Campinas/São Paulo region of Brazil. It:
1. Scrapes job listings from ~25 companies using Playwright
2. Saves results to Supabase
3. Classifies jobs as tech/non-tech via keyword matching and Gemini AI fallback
4. Sends a daily newsletter via Resend to subscribers

## Running the project

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run the full pipeline (scrape → filter → newsletter)
python app.py

# Run a single scraper test (headless=False, isolated SQLite DB)
python src/test/unit_test/test_bosch.py

# Run only the smart funnel (classification step)
python src/database/processa_funil.py

# Send newsletter manually
python src/newsletter/enviar_newsletter.py --dev   # dev mode: sends only to subscriber id=1
python src/newsletter/enviar_newsletter.py         # production: sends to all subscribers

# Manage subscribers
python src/newsletter/gerenciar_assinantes.py
```

## Required `.env` variables

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
GEMINI_API_KEY=
RESEND_API_KEY=
EMAIL_FROM=noreply@zerodezenovejobs.com.br
ENV=dev   # "dev" sends newsletter only to subscriber id=1; "prod" sends to all
```

## Architecture

### Data flow
`app.py` orchestrates: scrapers → `database.salvar_vaga()` → `processar_funil()` → `enviar_emails()`

### Supabase tables
- `vagas` — active job listings (deduplicated by `url_vaga`)
- `vagas_filtradas` — jobs that passed the tech funnel
- `vagas_removidas` — jobs no longer found on company sites
- `assinantes` — newsletter subscribers with `token_cancelamento` for unsubscribe links

At the end of each run, `finalizar_ciclo_scraping()` moves any `vagas` row whose `ultima_atualizacao` is before today into `vagas_removidas` and deletes it from `vagas` and `vagas_filtradas`.

### Scraper contract
Every module in `src/scrapers/` must export a single function:
```python
def raspar() -> list[dict]:
    # returns list of dicts with keys: empresa, titulo, localizacao, modelo_trabalho, url_vaga
```

Scrapers use `EMPRESA_URLS` and `SCRAPER_CONFIG` from `config/settings.py`. Most use Playwright (`sync_playwright`); a few use `requests` + BeautifulSoup.

### Smart funnel (`src/filtro_funil.py` + `src/database/processa_funil.py`)
Three-stage classification:
1. **NON_TECH_KEYWORDS match** → classified as `non-tech`, skipped
2. **TECH_KEYWORDS match** → classified as `tech funil`, saved to `vagas_filtradas`
3. **No match (dúvida)** → sent to Gemini API in batches of 20 → `tech IA` or `non-tech`

### Newsletter
Templates are Jinja2 HTML files in `src/templates/`. The newsletter renders today's new tech jobs and the full active job count, with a per-subscriber unsubscribe token embedded in each email.

## Adding a new scraper

1. Create `src/scrapers/NewCompany.py` implementing `raspar()`
2. Add the URL to `EMPRESA_URLS` in `config/settings.py`
3. Add an entry to `SCRAPERS_ATIVOS` in `config/settings.py`
4. Import the module and add it to `SCRAPERS_MAP` in `app.py`
5. Copy `src/test/unit_test/TEMPLATE_TEST.py` → `test_newcompy.py` and adapt it

## Testing scrapers

Unit tests in `src/test/unit_test/` use an isolated SQLite DB (not Supabase) so they don't pollute production data. Each test sets `headless=False` for visual debugging. Run them directly as scripts, not via pytest.

```bash
python src/test/unit_test/test_generalmotors.py
```
