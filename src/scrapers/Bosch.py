from playwright.sync_api import sync_playwright
from random import uniform
from urllib.parse import quote
from config.settings import SCRAPER_CONFIG, EMPRESA_URLS

EMPRESA = "Bosch"
BASE_URL = EMPRESA_URLS["Bosch"]
LOCATION = "Campinas, BR"

def _montar_url():
    return f"{BASE_URL}?search=&page=0&location={quote(LOCATION)}"

def raspar():
    print(f"Iniciando scraper {EMPRESA} (Playwright, location={LOCATION})")
    delay_min = SCRAPER_CONFIG.get("delay_min", 0.5)
    delay_max = SCRAPER_CONFIG.get("delay_max", 1.5)

    vagas = []
    vistos = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=SCRAPER_CONFIG.get("headless", False))
        context = browser.new_context(user_agent=SCRAPER_CONFIG.get("user_agent"))
        page = context.new_page()

        url = _montar_url()
        page.goto(url, timeout=SCRAPER_CONFIG.get("timeout", 60000))
        page.wait_for_load_state("domcontentloaded")

        # Expande todas as páginas clicando em "Mostrar mais empregos"
        while True:
            try:
                show_more = page.locator("a.js-more")
                if show_more.count() == 0 or not show_more.is_visible():
                    break
                show_more.click()
                page.wait_for_timeout(int(uniform(delay_min, delay_max) * 1000))
            except Exception:
                break

        # Coleta vagas
        itens = page.locator("li.opening-job")
        total = itens.count()
        print(f"Total de elementos de vaga encontrados: {total}")

        for i in range(total):
            item = itens.nth(i)
            try:
                titulo = item.locator("h4.details-title").inner_text().strip()
                href = item.locator("a.link--block").get_attribute("href") or ""
                if not href:
                    continue
                if href.startswith("/"):
                    href = "https://jobs.smartrecruiters.com" + href

                if href in vistos:
                    continue
                vistos.add(href)

                modelo = ""
                try:
                    modelo = item.locator("p.details-desc span").first.inner_text().strip()
                except Exception:
                    pass

                vagas.append({
                    "empresa": EMPRESA,
                    "titulo": titulo,
                    "localizacao": "Campinas",
                    "modelo_trabalho": modelo,
                    "url_vaga": href
                })
            except Exception:
                continue

        browser.close()

    print(f"Total coletado {EMPRESA}: {len(vagas)} vagas")
    return vagas