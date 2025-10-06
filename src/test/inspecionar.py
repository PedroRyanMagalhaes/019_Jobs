import asyncio
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from playwright.async_api import async_playwright, Page, Response

URL = "https://ciandt.com/br/pt-br/carreiras/oportunidades"
OUT_DIR = Path(__file__).parent / "ciandt_dump"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_JSON_PATTERNS = [
    r"/api/.*",
    r"/wp-json/.*",
    r"/graphql",
    r"/v1/.*",
]

def looks_like_api(url: str) -> bool:
    return any(re.search(p, url) for p in API_JSON_PATTERNS)

async def click_load_more(page: Page, max_cycles: int = 30):
    """Clica em botões de 'carregar mais' se existirem."""
    for i in range(max_cycles):
        # Ajuste seletor se necessário após inspecionar HTML salvo
        candidates = [
            "text=Carregar mais",
            "button:has-text('Carregar mais')",
            "text=Mostrar mais",
        ]
        clicked = False
        for sel in candidates:
            try:
                btn = await page.query_selector(sel)
                if btn and await btn.is_enabled():
                    await btn.click()
                    await page.wait_for_timeout(1200)
                    clicked = True
                    break
            except Exception:
                pass
        if not clicked:
            break

async def gentle_scroll(page: Page, steps: int = 15, delay: int = 250):
    height_prev = 0
    for _ in range(steps):
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
        await page.wait_for_timeout(delay)
        height_now = await page.evaluate("document.body.scrollHeight")
        if height_now == height_prev:
            break
        height_prev = height_now

async def main():
    api_requests: List[Dict] = []
    api_responses: List[Dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/118.0.0.0 Safari/537.36",
            locale="pt-BR",
        )

        page = await context.new_page()

        # Captura requisições
        page.on("request", lambda req: (
            api_requests.append({
                "url": req.url,
                "method": req.method,
                "resource_type": req.resource_type,
            }) if looks_like_api(req.url) else None
        ))

        async def handle_response(resp: Response):
            url = resp.url
            if looks_like_api(url):
                ctype = resp.headers.get("content-type", "")
                if "application/json" in ctype or url.endswith(".json"):
                    try:
                        data = await resp.json()
                        api_responses.append({
                            "url": url,
                            "status": resp.status,
                            "json": data
                        })
                    except Exception:
                        pass
        page.on("response", lambda r: asyncio.create_task(handle_response(r)))

        print("[*] Acessando página...")
        start_time = time.time()
        await page.goto(URL, wait_until="domcontentloaded")

        # Salva HTML inicial (antes de interações)
        raw_initial = await page.content()
        (OUT_DIR / "html_inicial.html").write_text(raw_initial, encoding="utf-8")
        print("[*] HTML inicial salvo -> html_inicial.html")

        # Aguarda algum contêiner provável de vagas (ajuste após inspecionar)
        possible_selectors = [
            "[class*='job']",
            "[class*='vaga']",
            "section:has(h2)",
            "div:has-text('Oportunidades')",
        ]
        for sel in possible_selectors:
            try:
                await page.wait_for_selector(sel, timeout=4000)
                break
            except Exception:
                continue

        # Scroll + carregar mais
        await gentle_scroll(page)
        await click_load_more(page)
        await gentle_scroll(page)

        # Aguarda rede acalmar um pouco
        await page.wait_for_timeout(2000)

        # HTML final
        final_html = await page.content()
        (OUT_DIR / "html_final.html").write_text(final_html, encoding="utf-8")
        print("[*] HTML final salvo -> html_final.html")

        # Salva requisições API detectadas
        (OUT_DIR / "api_requests.json").write_text(
            json.dumps(api_requests, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        (OUT_DIR / "api_responses.json").write_text(
            json.dumps(api_responses, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        # Gera um arquivo com possíveis seletores de itens
        selectors_hint = await extract_selector_hints(page)
        (OUT_DIR / "possiveis_seletores.txt").write_text(
            "\n".join(selectors_hint), encoding="utf-8"
        )

        print(f"[*] Possíveis seletores salvos -> possiveis_seletores.txt")
        print(f"[*] Tempo total: {time.time() - start_time:.1f}s")
        await browser.close()

async def extract_selector_hints(page: Page) -> List[str]:
    js = r"""
    (() => {
      const out = new Set();
      const nodes = Array.from(document.querySelectorAll("a, div, li, article, section"));
      nodes.slice(0, 3000).forEach(n => {
        const txt = (n.innerText || "").trim();
        if (!txt) return;
        if (/vaga|job|oportunidade|desenvolvedor|developer|engineer|analista|tech/i.test(txt)) {
          // monta caminho simples
            let path = n.tagName.toLowerCase();
            if (n.id) path += "#" + n.id;
            if (n.className && typeof n.className === "string") {
              const cls = n.className.trim().split(/\s+/).slice(0,3).join(".");
              if (cls) path += "." + cls;
            }
            out.add(path);
        }
      });
      return Array.from(out).slice(0,50);
    })();
    """
    try:
        hints = await page.evaluate(js)
        return hints
    except Exception:
        return []

if __name__ == "__main__":
    asyncio.run(main())