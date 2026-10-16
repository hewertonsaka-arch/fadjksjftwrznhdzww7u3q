import os
import tempfile
from analyzer import ResultadoAnalise
from loader import minutes_to_time_str
from image_fallback import gerar_imagem_fallback

def _fmt_aderencia(v: float) -> str:
    return f"{int(v)}%"

def _fmt_tempo(v: int | float) -> str:
    return f"{int(v)}min"

def gerar_imagem_html(resultado: ResultadoAnalise, tipo: str = "anterior") -> bytes:
    """
    Gera uma imagem rica (PNG) baseada em HTML/CSS usando html2image.
    Suporta os modos:
      - "anterior": Resumo dia anterior (com check-in e check-out pela média)
      - "atual": Resumo dia atual (com check-in fixo, sem check-out e nomenclaturas do dia)
    Retorna os bytes da imagem gerada.
    """
    
    # CSS Moderno (Estilo Card Claro)
    css = """
    body {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: #f8fafc;
        margin: 0;
        padding: 40px;
        color: #1e293b;
    }
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        padding: 30px;
        max-width: 700px;
        margin: 0 auto;
        border-top: 5px solid #3b82f6;
    }
    .header {
        text-align: center;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 1px solid #e2e8f0;
    }
    .header h1 {
        margin: 0;
        color: #0f172a;
        font-size: 24px;
    }
    .header p {
        margin: 5px 0 0 0;
        color: #64748b;
        font-size: 16px;
    }
    .section {
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }
    .icon {
        margin-right: 8px;
        font-size: 20px;
    }
    ul {
        margin: 0;
        padding-left: 25px;
        list-style-type: none;
    }
    li {
        position: relative;
        margin-bottom: 5px;
        font-size: 15px;
        color: #334155;
    }
    li::before {
        content: "•";
        color: #94a3b8;
        position: absolute;
        left: -15px;
        font-weight: bold;
    }
    .name {
        font-weight: 700;
        color: #0f172a;
    }
    .value {
        font-weight: 600;
    }
    .text-red { color: #ef4444; }
    .text-green { color: #10b981; }
    .text-blue { color: #3b82f6; }
    .text-orange { color: #f59e0b; }
    .text-purple { color: #8b5cf6; }
    .text-slate { color: #64748b; }
    """

    nome_gestor = resultado.gestor_selecionado if resultado.gestor_selecionado else "Geral"
    
    html_parts = []
    html_parts.append(f"""
    <div class="card">
        <div class="header">
            <h1>Resumo de Visitas {nome_gestor}</h1>
            <p>Período apurado: <strong>{resultado.periodo}</strong></p>
        </div>
    """)

    if tipo == "atual":
        # --- Resumo Dia Atual ---
        # 1. Check-in fixo
        if resultado.checkin_acima_fixo:
            hora_fixa_ci = minutes_to_time_str(resultado.limiar_checkin_fixo_min).replace(":", "h")
            html_parts.append(f"""
            <div class="section">
                <div class="section-title text-blue">
                    <span class="icon">📤</span> Check-in acima das {hora_fixa_ci}:
                </div>
                <ul>
            """)
            for vm in resultado.checkin_acima_fixo:
                html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
            html_parts.append("</ul></div>")

        # 2. Check-out fixo
        if resultado.checkout_abaixo_fixo:
            hora_fixa_co = minutes_to_time_str(resultado.limiar_checkout_fixo_min).replace(":", "h")
            html_parts.append(f"""
            <div class="section">
                <div class="section-title text-orange">
                    <span class="icon">📥</span> Check-out abaixo das {hora_fixa_co}:
                </div>
                <ul>
            """)
            for vm in resultado.checkout_abaixo_fixo:
                html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
            html_parts.append("</ul></div>")

        # 3. Visitas não realizadas Até o Momento
        if resultado.nao_realizadas:
            html_parts.append("""
            <div class="section">
                <div class="section-title text-red">
                    <span class="icon">❌</span> Visitas não realizadas Ate o Momento:
                </div>
                <ul>
            """)
            for vm in resultado.nao_realizadas:
                html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
            html_parts.append("</ul></div>")

        # 3. Sem Visitas Ate o Momento (aderência 0%)
        if resultado.nao_realizou_visitas:
            html_parts.append("""
            <div class="section">
                <div class="section-title text-purple">
                    <span class="icon">🚫</span> Sem Visitas Ate o Momento:
                </div>
                <ul>
            """)
            for nome in resultado.nao_realizou_visitas:
                html_parts.append(f'<li><span class="name">{nome}</span></li>')
            html_parts.append("</ul></div>")

        # 4. Visitas Inativadas (aderência NaN)
        if resultado.visitas_canceladas:
            html_parts.append("""
            <div class="section">
                <div class="section-title text-slate">
                    <span class="icon">🗑️</span> Visitas Inativadas:
                </div>
                <ul>
            """)
            for nome in resultado.visitas_canceladas:
                html_parts.append(f'<li><span class="name">{nome}</span></li>')
            html_parts.append("</ul></div>")

    else:
        # --- Resumo Dia Anterior ---
        # 1. Check-in acima da média
        if resultado.acima_checkin:
            media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
            html_parts.append(f"""
            <div class="section">
                <div class="section-title text-blue">
                    <span class="icon">📤</span> Check-in acima da média do time [{media_ci_str}]:
                </div>
                <ul>
            """)
            for vm in resultado.acima_checkin:
                html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
            html_parts.append("</ul></div>")

        # 2. Check-out abaixo da média
        if resultado.abaixo_checkout:
            media_co_str = minutes_to_time_str(resultado.media_checkout_min)
            html_parts.append(f"""
            <div class="section">
                <div class="section-title text-orange">
                    <span class="icon">📥</span> Check-out abaixo da média do time [{media_co_str}]:
                </div>
                <ul>
            """)
            for vm in resultado.abaixo_checkout:
                html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
            html_parts.append("</ul></div>")

        # 3. Visitas não realizadas
        if resultado.nao_realizadas:
            html_parts.append("""
            <div class="section">
                <div class="section-title text-red">
                    <span class="icon">❌</span> Visitas não realizadas:
                </div>
                <ul>
            """)
            for vm in resultado.nao_realizadas:
                html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
            html_parts.append("</ul></div>")

        # 4. Não Realizou Visitas (aderência 0%)
        if resultado.nao_realizou_visitas:
            html_parts.append("""
            <div class="section">
                <div class="section-title text-purple">
                    <span class="icon">🚫</span> Não Realizou Visitas:
                </div>
                <ul>
            """)
            for nome in resultado.nao_realizou_visitas:
                html_parts.append(f'<li><span class="name">{nome}</span></li>')
            html_parts.append("</ul></div>")

        # 5. Visitas Inativadas (aderência NaN)
        if resultado.visitas_canceladas:
            html_parts.append("""
            <div class="section">
                <div class="section-title text-slate">
                    <span class="icon">🗑️</span> Visitas Inativadas:
                </div>
                <ul>
            """)
            for nome in resultado.visitas_canceladas:
                html_parts.append(f'<li><span class="name">{nome}</span></li>')
            html_parts.append("</ul></div>")

    html_parts.append("</div>")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        {''.join(html_parts)}
    </body>
    </html>
    """

    # Tentativa de renderizar com html2image; fallback gracioso via Pillow
    try:
        from html2image import Html2Image
        with tempfile.TemporaryDirectory() as tmpdirname:
            hti = Html2Image(size=(800, 1000))
            hti.output_path = tmpdirname
            filename = "relatorio.png"
            hti.screenshot(html_str=html_content, save_as=filename)
            filepath = os.path.join(tmpdirname, filename)
            with open(filepath, "rb") as f:
                return f.read()

    except Exception:
        secoes: list[tuple[str, list[str]]] = []
        if tipo == "atual":
            if resultado.checkin_acima_fixo:
                hora_fixa_ci = minutes_to_time_str(resultado.limiar_checkin_fixo_min).replace(":", "h")
                secoes.append((
                    f"Check-in acima das {hora_fixa_ci}",
                    [f"{vm.nome} — {vm.valor}" for vm in resultado.checkin_acima_fixo],
                ))
            if resultado.checkout_abaixo_fixo:
                hora_fixa_co = minutes_to_time_str(resultado.limiar_checkout_fixo_min).replace(":", "h")
                secoes.append((
                    f"Check-out abaixo das {hora_fixa_co}",
                    [f"{vm.nome} — {vm.valor}" for vm in resultado.checkout_abaixo_fixo],
                ))
            if resultado.nao_realizadas:
                secoes.append((
                    "Visitas não realizadas Ate o Momento",
                    [f"{vm.nome} — {vm.valor}" for vm in resultado.nao_realizadas],
                ))
            if resultado.nao_realizou_visitas:
                secoes.append((
                    "Sem Visitas Ate o Momento",
                    [f"{nome}" for nome in resultado.nao_realizou_visitas],
                ))
            if resultado.visitas_canceladas:
                secoes.append((
                    "Visitas Inativadas",
                    [f"{nome}" for nome in resultado.visitas_canceladas],
                ))
        else:
            if resultado.acima_checkin:
                media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
                secoes.append((
                    f"Check-in acima da média do time [{media_ci_str}]",
                    [f"{vm.nome} — {vm.valor}" for vm in resultado.acima_checkin],
                ))
            if resultado.abaixo_checkout:
                media_co_str = minutes_to_time_str(resultado.media_checkout_min)
                secoes.append((
                    f"Check-out abaixo da média do time [{media_co_str}]",
                    [f"{vm.nome} — {vm.valor}" for vm in resultado.abaixo_checkout],
                ))
            if resultado.nao_realizadas:
                secoes.append((
                    "Visitas não realizadas",
                    [f"{vm.nome} — {vm.valor}" for vm in resultado.nao_realizadas],
                ))
            if resultado.nao_realizou_visitas:
                secoes.append((
                    "Não Realizou Visitas",
                    [f"{nome}" for nome in resultado.nao_realizou_visitas],
                ))
            if resultado.visitas_canceladas:
                secoes.append((
                    "Visitas Inativadas",
                    [f"{nome}" for nome in resultado.visitas_canceladas],
                ))

        return gerar_imagem_fallback(
            f"Resumo de Visitas {nome_gestor}", resultado.periodo, secoes
        )
