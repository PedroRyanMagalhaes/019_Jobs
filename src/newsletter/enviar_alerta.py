"""
Envia email de alerta para o subscriber id=1 quando scrapers retornam 0 vagas.
"""
import os
import resend
from datetime import datetime
from dotenv import load_dotenv
from src.newsletter.gerenciar_assinantes import buscar_assinante_dev

load_dotenv()


def enviar_alerta_scrapers_vazios(empresas_vazias: list[tuple[str, str]]):
    """
    empresas_vazias: lista de (nome_empresa, url_origem)
    """
    resend.api_key = os.getenv("RESEND_API_KEY")
    email_from = os.getenv("EMAIL_FROM", "noreply@zerodezenovejobs.com.br")

    if not resend.api_key:
        print("⚠️  RESEND_API_KEY não encontrada — alerta não enviado.")
        return

    try:
        assinante = buscar_assinante_dev()[0]
    except Exception as e:
        print(f"⚠️  Não encontrou assinante id=1: {e}")
        return

    data_hoje = datetime.now().strftime("%d/%m/%Y")

    itens_html = ""
    for nome, url in empresas_vazias:
        itens_html += f"""
        <div style="background-color:#1a1b26;border-left:3px solid #ff5555;margin-bottom:14px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#f8f8f2;font-size:15px;font-weight:600;">{nome}</span>
            <a href="{url}" style="color:#ff5555;text-decoration:none;font-size:12px;border:1px solid #ff5555;padding:6px 16px;white-space:nowrap;">
                VERIFICAR -&gt;
            </a>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:'Courier New',Courier,monospace;background-color:#0f0f13;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0f0f13;">
<tr><td align="center" style="padding:40px 10px;">
<table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color:#16161e;max-width:600px;width:100%;">

    <tr>
        <td style="background-color:#1a1b26;padding:10px 20px;border-bottom:1px solid #2f334d;">
            <span style="height:10px;width:10px;background-color:#ff5555;border-radius:50%;display:inline-block;margin-right:6px;"></span>
            <span style="height:10px;width:10px;background-color:#f1fa8c;border-radius:50%;display:inline-block;margin-right:6px;"></span>
            <span style="height:10px;width:10px;background-color:#50fa7b;border-radius:50%;display:inline-block;"></span>
        </td>
    </tr>

    <tr>
        <td style="padding:40px 40px 20px 40px;">
            <h1 style="color:#ff5555;margin:0;font-size:22px;font-weight:400;letter-spacing:-1px;">
                <span style="color:#6272a4;">&lt;</span>019_Jobs<span style="color:#6272a4;">/&gt;</span>
                &nbsp;⚠️ Alerta
            </h1>
            <p style="color:#6279c0;margin:10px 0 0 0;font-size:12px;text-transform:uppercase;letter-spacing:2px;">
                {data_hoje} &bull; {len(empresas_vazias)} empresa(s) sem vagas
            </p>
        </td>
    </tr>

    <tr>
        <td style="padding:0 40px;">
            <div style="height:1px;background:linear-gradient(90deg,#ff5555 0%,transparent 100%);opacity:0.4;"></div>
        </td>
    </tr>

    <tr>
        <td style="padding:30px 40px 10px 40px;">
            <p style="color:#6272a4;font-size:13px;margin:0 0 20px 0;">
                // As empresas abaixo retornaram <strong style="color:#ff5555;">0 vagas</strong> no scraping de hoje.<br>
                // Verifique se é bug ou se o site realmente está vazio.
            </p>
            {itens_html}
        </td>
    </tr>

    <tr>
        <td style="background-color:#13131a;padding:24px;text-align:center;border-top:1px solid #1f202e;">
            <p style="color:#44475a;font-size:11px;margin:0;">019_Jobs — Alerta automático de monitoramento</p>
        </td>
    </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    try:
        params = {
            "from": f"019_JOBS Alerta <{email_from}>",
            "to": [assinante["email"]],
            "subject": f"⚠️ {len(empresas_vazias)} scrapers vazios • {data_hoje}",
            "html": html,
        }
        resend.Emails.send(params)
        print(f"📧 Alerta enviado para {assinante['email']} ({len(empresas_vazias)} empresas).")
    except Exception as e:
        print(f"❌ Erro ao enviar alerta: {e}")
