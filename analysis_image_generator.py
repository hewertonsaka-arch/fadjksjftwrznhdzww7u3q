# analysis_image_generator.py
# Gera imagem PNG da Análise Criteriosa (pontos positivos, negativos e insights).

from __future__ import annotations

import os
import tempfile

from analyzer import ResultadoAnalise
from insights import gerar_insights
from loader import minutes_to_time_str


def _fmt_aderencia(v: float) -> str:
    return f"{int(v)}%"


def _fmt_tempo(v: int | float) -> str:
    return f"{int(v)} min"


def _build_card_html(titulo: str, items: list[str], cor: str, icone: str) -> str:
    """Monta um card HTML de pontos (positivos ou negativos)."""
    if not items:
        return ""
    itens_html = "".join(f"<li>{item}</li>" for item in items)
    return f"""
    <div class="card card-{cor}">
        <div class="card-title">
            <span class="card-icon">{icone}</span> {titulo}
        </div>
        <ul>{itens_html}</ul>
    </div>
    """


def gerar_imagem_analise(resultado: ResultadoAnalise) -> bytes:
    """
    Gera uma imagem PNG da Análise Criteriosa.
    Retorna os bytes da imagem.
    """
    insights = gerar_insights(resultado)
    nome_gestor = resultado.gestor_selecionado if resultado.gestor_selecionado else "Geral"

    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: 'Inter', 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 36px;
        color: #e2e8f0;
        min-height: 100%;
    }
    .wrapper { max-width: 760px; margin: 0 auto; }
    .header {
        text-align: center;
        margin-bottom: 28px;
        padding-bottom: 20px;
        border-bottom: 1px solid #334155;
    }
    .header h1 { font-size: 22px; font-weight: 700; color: #f1f5f9; }
    .header p  { font-size: 14px; color: #94a3b8; margin-top: 6px; }

    h2 {
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 22px 0 12px;
        color: #94a3b8;
    }

    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 8px; }

    .card {
        border-radius: 10px;
        padding: 16px 18px;
        border-left: 4px solid transparent;
    }
    .card-verde  { background: #052e16; border-color: #22c55e; }
    .card-vermelho { background: #450a0a; border-color: #ef4444; }
    .card-amarelo  { background: #1c1400; border-color: #f59e0b; }

    .card-title {
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 8px;
        color: #f1f5f9;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .card-icon { font-size: 16px; }
    ul { padding-left: 16px; }
    li {
        font-size: 12px;
        color: #cbd5e1;
        margin-bottom: 4px;
        line-height: 1.4;
    }

    /* Insights */
    .insight {
        border-radius: 10px;
        padding: 13px 16px;
        margin-bottom: 10px;
        border-left: 4px solid transparent;
    }
    .insight-positivo { background: #052e16; border-color: #22c55e; }
    .insight-negativo { background: #450a0a; border-color: #ef4444; }
    .insight-atencao  { background: #1c1400; border-color: #f59e0b; }
    .insight-neutro   { background: #0f172a; border-color: #64748b; }

    .insight-titulo {
        font-size: 13px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 4px;
    }
    .insight-detalhe { font-size: 12px; color: #94a3b8; line-height: 1.5; }

    /* Ranking */
    .ranking-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
    .ranking-table th {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #64748b;
        padding: 6px 8px;
        text-align: left;
        border-bottom: 1px solid #1e293b;
    }
    .ranking-table td {
        font-size: 12px;
        color: #cbd5e1;
        padding: 6px 8px;
        border-bottom: 1px solid #1e293b;
    }
    .rank-bar-bg {
        background: #1e293b;
        border-radius: 4px;
        height: 8px;
        min-width: 80px;
    }
    .rank-bar-fill {
        height: 8px;
        border-radius: 4px;
        background: linear-gradient(90deg, #3b82f6, #6366f1);
    }
    .rank-bar-fill-red {
        height: 8px;
        border-radius: 4px;
        background: linear-gradient(90deg, #ef4444, #f97316);
    }

    .footer {
        margin-top: 22px;
        padding-top: 14px;
        border-top: 1px dashed #334155;
        font-size: 11px;
        color: #475569;
        text-align: center;
    }
    """

    # ---- Pontos Positivos ----
    positivos_html = ""

    # Aderência positiva
    if resultado.acima_aderencia:
        items = [f"<b>{vm.nome}</b> — {_fmt_aderencia(vm.valor)}" for vm in resultado.acima_aderencia]
        positivos_html += _build_card_html(
            f"Aderência acima da média ({_fmt_aderencia(resultado.media_aderencia)})",
            items, "verde", "✅"
        )

    # Check-in pontual
    if resultado.abaixo_checkin:
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.abaixo_checkin]
        positivos_html += _build_card_html(
            f"Check-in pontual (antes de {media_ci_str})",
            items, "verde", "⏰"
        )

    # Tempo no cliente positivo
    if resultado.acima_tempo:
        items = [f"<b>{vm.nome}</b> — {_fmt_tempo(vm.valor)}" for vm in resultado.acima_tempo]
        positivos_html += _build_card_html(
            f"Bom tempo no cliente (≥ {_fmt_tempo(resultado.limiar_tempo)})",
            items, "verde", "🕐"
        )

    # Sem faltas
    if resultado.sem_faltas:
        items = [f"<b>{nome}</b>" for nome in resultado.sem_faltas]
        positivos_html += _build_card_html("Zero visitas não realizadas", items, "verde", "🎯")

    # ---- Pontos Negativos ----
    negativos_html = ""

    if resultado.abaixo_aderencia:
        media_str = _fmt_aderencia(resultado.media_aderencia)
        items = [f"<b>{vm.nome}</b> — {_fmt_aderencia(vm.valor)}" for vm in resultado.abaixo_aderencia]
        negativos_html += _build_card_html(
            f"Aderência abaixo da média ({media_str})", items, "vermelho", "🔻"
        )

    if resultado.acima_checkin:
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.acima_checkin]
        negativos_html += _build_card_html(
            f"Check-in tardio (depois de {media_ci_str})", items, "vermelho", "📤"
        )

    if resultado.abaixo_checkout:
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.abaixo_checkout]
        negativos_html += _build_card_html(
            f"Check-out antecipado (antes de {media_co_str})", items, "vermelho", "📥"
        )

    if resultado.abaixo_tempo:
        items = [f"<b>{vm.nome}</b> — {_fmt_tempo(vm.valor)}" for vm in resultado.abaixo_tempo]
        negativos_html += _build_card_html(
            f"Tempo insuficiente no cliente (< {_fmt_tempo(resultado.limiar_tempo)})",
            items, "vermelho", "⏳"
        )

    if resultado.nao_realizadas:
        items = [f"<b>{vm.nome}</b> — {vm.valor} visita(s)" for vm in resultado.nao_realizadas]
        negativos_html += _build_card_html("Visitas não realizadas", items, "vermelho", "❌")

    if resultado.somente_remota:
        items = [f"<b>{nome}</b>" for nome in resultado.somente_remota]
        negativos_html += _build_card_html(
            "Apenas visitas remotas (ponto crítico)", items, "amarelo", "⚠️"
        )

    # ---- Ranking de Aderência ----
    max_ad = resultado.ranking_aderencia[0].aderencia if resultado.ranking_aderencia else 100
    ranking_rows = ""
    for i, v in enumerate(resultado.ranking_aderencia, 1):
        pct_bar = int(v.aderencia / max_ad * 100) if max_ad > 0 else 0
        ranking_rows += f"""
        <tr>
            <td style="color:#64748b;width:24px">{i}</td>
            <td><b>{v.nome}</b></td>
            <td style="color:#6366f1;font-weight:700;width:50px">{int(v.aderencia)}%</td>
            <td style="width:120px">
                <div class="rank-bar-bg">
                    <div class="rank-bar-fill" style="width:{pct_bar}%"></div>
                </div>
            </td>
        </tr>"""

    # ---- Insights ----
    insights_html = ""
    for ins in insights:
        insights_html += f"""
        <div class="insight insight-{ins['tipo']}">
            <div class="insight-titulo">{ins['icone']} {ins['titulo']}</div>
            <div class="insight-detalhe">{ins['detalhe']}</div>
        </div>"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>{css}</style>
</head>
<body>
<div class="wrapper">
    <div class="header">
        <h1>🔍 Análise Criteriosa — {nome_gestor}</h1>
        <p>Período: <strong>{resultado.periodo}</strong> &nbsp;|&nbsp; {resultado.total_vendedores} vendedores analisados</p>
    </div>

    <h2>🟢 Pontos Positivos</h2>
    <div class="grid">{positivos_html or '<p style="color:#64748b;font-size:13px">Nenhum ponto positivo identificado.</p>'}</div>

    <h2>🔴 Pontos de Atenção</h2>
    <div class="grid">{negativos_html or '<p style="color:#64748b;font-size:13px">Nenhum ponto negativo identificado.</p>'}</div>

    <h2>📊 Ranking de Aderência à Rota</h2>
    <table class="ranking-table">
        <thead>
            <tr>
                <th>#</th><th>Vendedor</th><th>Aderência</th><th>Barra</th>
            </tr>
        </thead>
        <tbody>{ranking_rows}</tbody>
    </table>

    <h2>💡 Insights para Tomada de Decisão</h2>
    {insights_html}

    <div class="footer">
        ⚠️ Visitas remotas não são consideradas no cálculo da aderência à rota.
    </div>
</div>
</body>
</html>"""

    try:
        # A criação de Html2Image pode falhar em ambientes sem Chrome/Chromium
        from html2image import Html2Image
        with tempfile.TemporaryDirectory() as tmpdir:
            hti = Html2Image(size=(800, 2200))
            hti.output_path = tmpdir
            filename = "analise_criteriosa.png"
            hti.screenshot(html_str=html_content, save_as=filename)
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, "rb") as f:
                return f.read()

    except Exception:
        # Fallback simples: gerar uma imagem textual com Pillow para não quebrar na nuvem
        import re
        from io import BytesIO
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            raise

        def _strip_emoji(text: str) -> str:
            return "".join(ch for ch in text if ord(ch) <= 0xFFFF)

        # Extrai texto bruto do HTML e compacta espaços
        text = re.sub(r"<[^>]+>", "", html_content)
        text = re.sub(r"\s+", " ", text).strip()

        # Layout básico
        width = 800
        font = ImageFont.load_default()
        max_chars_per_line = 90
        lines = [ _strip_emoji(text[i:i+max_chars_per_line]) for i in range(0, len(text), max_chars_per_line) ]
        line_height = font.getsize("A")[1] + 4
        height = max(600, line_height * len(lines) + 40)

        img = Image.new("RGB", (width, height), (15, 23, 42))
        draw = ImageDraw.Draw(img)
        x, y = 20, 20
        fill = (225, 229, 241)
        for line in lines:
            if not line:
                y += line_height
                continue
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height

        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
