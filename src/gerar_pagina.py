"""
Gera docs/index.html com todas as vagas ativas (vagas_filtradas) e faz git push.
Chamado no final de app.py a cada execução.
"""
import os
import subprocess
from datetime import datetime
from src.database.supabase_client import get_supabase


def buscar_todas_vagas_ativas():
    sb = get_supabase()
    res = sb.table("vagas_filtradas").select(
        "titulo, empresa, localizacao, modelo_trabalho, url_vaga, data_coleta"
    ).order("data_coleta", desc=True).execute()
    return res.data


_MODELO_NORMALIZADO = {
    "hibrido": "Híbrido",
    "híbrido": "Híbrido",
    "remoto": "Remoto",
    "presencial": "Presencial",
}

def _normalizar_modelo(modelo):
    return _MODELO_NORMALIZADO.get((modelo or "").strip().lower(), (modelo or "").strip())

def _escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def gerar_html(vagas):
    empresas = sorted(set(v["empresa"] for v in vagas))
    modelos = sorted(set(_normalizar_modelo(v.get("modelo_trabalho")) for v in vagas if v.get("modelo_trabalho")))

    cards_html = ""
    for v in vagas:
        titulo = _escape(v["titulo"])
        empresa = _escape(v["empresa"])
        loc = _escape(v.get("localizacao") or "Não especificado")
        modelo = _escape(_normalizar_modelo(v.get("modelo_trabalho")))
        url = _escape(v["url_vaga"])
        modelo_tag = f'<span class="sep"> </span><span class="modelo">{modelo}</span>' if modelo else ""
        cards_html += f"""
        <div class="vaga-card" data-empresa="{empresa}" data-modelo="{modelo}">
            <h3 class="titulo">{titulo}</h3>
            <p class="empresa"><span class="arrow">&gt;</span> {empresa}</p>
            <div class="meta"><span class="loc">{loc}</span>{modelo_tag}</div>
            <a href="{url}" target="_blank" class="btn-vaga">ABRIR VAGA -&gt;</a>
        </div>"""

    empresa_opts = "".join(f'<option value="{_escape(e)}">{_escape(e)}</option>' for e in empresas)
    modelo_opts = "".join(f'<option value="{_escape(m)}">{_escape(m)}</option>' for m in modelos)
    total = len(vagas)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>019 Jobs — Vagas Tech Campinas</title>
    <style>
        *{{box-sizing:border-box;margin:0;padding:0}}
        body{{font-family:'Courier New',Courier,monospace;background:#0f0f13;color:#f8f8f2;min-height:100vh;padding:40px 16px}}
        .container{{max-width:700px;margin:0 auto}}
        .header{{background:#16161e;border-bottom:1px solid #2f334d}}
        .dots{{background:#1a1b26;padding:10px 20px;border-bottom:1px solid #2f334d}}
        .dot{{height:10px;width:10px;border-radius:50%;display:inline-block;margin-right:6px}}
        .dot-r{{background:#ff5555}}.dot-y{{background:#f1fa8c}}.dot-g{{background:#50fa7b}}
        .hcontent{{padding:40px 40px 30px}}
        h1{{color:#bd93f9;font-size:28px;font-weight:400;letter-spacing:-1px;margin-bottom:8px}}
        h1 .br{{color:#6272a4}}
        .subtitle{{color:#6279c0;font-size:12px;text-transform:uppercase;letter-spacing:2px}}
        .divider{{height:1px;background:linear-gradient(90deg,#bd93f9 0%,transparent 100%);opacity:.3;margin:0 40px}}
        .filters{{background:#16161e;padding:20px 40px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;border-bottom:1px solid #1f202e}}
        input[type=text],select{{background:#1a1b26;border:1px solid #2f334d;color:#f8f8f2;font-family:'Courier New',Courier,monospace;font-size:13px;padding:8px 12px;outline:none}}
        input[type=text]{{flex:1;min-width:160px}}
        input[type=text]::placeholder{{color:#44475a}}
        select{{min-width:130px;cursor:pointer}}
        select option{{background:#1a1b26}}
        .count{{color:#6272a4;font-size:12px;margin-left:auto;white-space:nowrap}}
        .cards{{background:#16161e;padding:30px 40px 40px}}
        .vaga-card{{background:#1a1b26;border-left:3px solid #bd93f9;margin-bottom:24px;padding:24px}}
        .vaga-card.hidden{{display:none}}
        .titulo{{color:#f8f8f2;font-size:17px;font-weight:600;line-height:1.4;margin-bottom:8px}}
        .empresa{{color:#8be9fd;font-size:14px;font-weight:bold;margin-bottom:12px}}
        .arrow{{color:#ffb86c;margin-right:5px}}
        .meta{{margin-bottom:18px}}
        .loc,.modelo{{color:#6279c0;font-size:13px}}
        .sep{{color:#44475a;margin:0 8px}}
        .btn-vaga{{display:inline-block;color:#bd93f9;text-decoration:none;font-size:12px;font-weight:bold;border:1px solid #bd93f9;padding:8px 22px}}
        .btn-vaga:hover{{background:#bd93f9;color:#0f0f13}}
        .empty{{text-align:center;padding:40px;border:1px dashed #44475a;color:#6272a4;font-size:14px;display:none}}
        .empty.show{{display:block}}
        .footer{{background:#13131a;padding:24px 40px;text-align:center;border-top:1px solid #1f202e}}
        .footer p{{color:#44475a;font-size:11px;line-height:1.8}}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="dots">
            <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
        </div>
        <div class="hcontent">
            <h1><span class="br">&lt;</span>019_Jobs<span class="br">/&gt;</span></h1>
            <p class="subtitle">Vagas Tech &mdash; Campinas e Região &nbsp;&bull;&nbsp; {agora} &nbsp;&bull;&nbsp; {total} vagas ativas</p>
        </div>
        <div class="divider"></div>
    </div>

    <div class="filters">
        <input type="text" id="search" placeholder="// buscar por título..." oninput="filtrar()">
        <select id="filtro-empresa" onchange="filtrar()">
            <option value="">Empresa</option>
            {empresa_opts}
        </select>
        <select id="filtro-modelo" onchange="filtrar()">
            <option value="">Modelo</option>
            {modelo_opts}
        </select>
        <span class="count" id="count">{total} de {total}</span>
    </div>

    <div class="cards" id="cards">
        {cards_html}
        <div class="empty" id="empty">// Nenhuma vaga encontrada com esses filtros.</div>
    </div>

    <div class="footer">
        <p>019_Jobs &mdash; Vagas tech em Campinas e região<br>
        Atualizado automaticamente a cada coleta.</p>
    </div>
</div>
<script>
    const total={total};
    function filtrar(){{
        const s=document.getElementById('search').value.toLowerCase();
        const e=document.getElementById('filtro-empresa').value;
        const m=document.getElementById('filtro-modelo').value;
        let n=0;
        document.querySelectorAll('.vaga-card').forEach(c=>{{
            const ok=(!s||c.querySelector('.titulo').textContent.toLowerCase().includes(s))
                   &&(!e||c.dataset.empresa===e)
                   &&(!m||c.dataset.modelo===m);
            c.classList.toggle('hidden',!ok);
            if(ok)n++;
        }});
        document.getElementById('count').textContent=n+' de '+total;
        document.getElementById('empty').classList.toggle('show',n===0);
    }}
</script>
</body>
</html>"""


def gerar_pagina():
    print("🌐 Gerando página estática de vagas...")
    vagas = buscar_todas_vagas_ativas()
    html = gerar_html(vagas)

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ docs/index.html gerado com {len(vagas)} vagas.")

    try:
        result = subprocess.run(["git", "add", "docs/index.html"], capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, "git add", result.stderr)

        # Verifica se há algo para commitar
        status = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if status.returncode == 0:
            print("ℹ️  Página sem alterações, push ignorado.")
            return

        subprocess.run(
            ["git", "commit", "-m", f"chore: atualiza vagas ativas [{datetime.now().strftime('%Y-%m-%d')}]"],
            check=True, capture_output=True, text=True
        )
        subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
        print("✅ Página publicada no GitHub Pages!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Erro no git push: {e.stderr or e}")
        print("    (Página gerada localmente — faça push manualmente.)")
    except FileNotFoundError:
        print("⚠️  Git não encontrado no PATH. Página gerada em docs/index.html.")


if __name__ == "__main__":
    gerar_pagina()
