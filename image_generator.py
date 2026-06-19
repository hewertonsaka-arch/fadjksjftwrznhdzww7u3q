import os
import tempfile
from html2image import Html2Image
from analyzer import ResultadoAnalise
from loader import minutes_to_time_str

def _fmt_aderencia(v: float) -> str:
    return f"{int(v)}%"

def _fmt_tempo(v: int | float) -> str:
    return f"{int(v)}min"

def gerar_imagem_html(resultado: ResultadoAnalise) -> bytes:
    """
    Gera uma imagem rica (PNG) baseada em HTML/CSS usando html2image.
    Retorna os bytes da imagem.
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
    .text-teal { color: #0d9488; }
    
    .footer {
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px dashed #cbd5e1;
        font-size: 13px;
        color: #64748b;
        text-align: center;
    }
    """

    # Montando as seções do HTML dinamicamente
    html_parts = []
    
    nome_gestor = resultado.gestor_selecionado if resultado.gestor_selecionado else "Geral"
    html_parts.append(f"""
    <div class="card">
        <div class="header">
            <h1>Resumo de Visitas {nome_gestor}</h1>
            <p>Período apurado: <strong>{resultado.periodo}</strong></p>
        </div>
    """)

    # 1. Aderência à rota
    if resultado.abaixo_aderencia:
        media_str = _fmt_aderencia(resultado.media_aderencia)
        html_parts.append(f"""
        <div class="section">
            <div class="section-title text-red">
                <span class="icon">🔻</span> Aderência à rota abaixo da média da equipe ({media_str}):
            </div>
            <ul>
        """)
        for vm in resultado.abaixo_aderencia:
            html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{_fmt_aderencia(vm.valor)}</span></li>')
        html_parts.append("</ul></div>")
    else:
        html_parts.append(f"""
        <div class="section">
            <div class="section-title text-green">
                <span class="icon">✅</span> Todos os vendedores estão acima ou na média de aderência à rota ({_fmt_aderencia(resultado.media_aderencia)}).
            </div>
        </div>
        """)

    # 2. Check-in acima da média
    if resultado.acima_checkin:
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        html_parts.append(f"""
        <div class="section">
            <div class="section-title text-blue">
                <span class="icon">📤</span> Check-in acima da média do time ({media_ci_str}):
            </div>
            <ul>
        """)
        for vm in resultado.acima_checkin:
            html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
        html_parts.append("</ul></div>")

    # 3. Check-out abaixo da média
    if resultado.abaixo_checkout:
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        html_parts.append(f"""
        <div class="section">
            <div class="section-title text-orange">
                <span class="icon">📥</span> Check-out abaixo da média do time ({media_co_str}):
            </div>
            <ul>
        """)
        for vm in resultado.abaixo_checkout:
            html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{vm.valor}</span></li>')
        html_parts.append("</ul></div>")

    # 4. Tempo no cliente
    if resultado.abaixo_tempo:
        html_parts.append("""
        <div class="section">
            <div class="section-title text-purple">
                <span class="icon">⏳</span> Tempo médio de permanência no cliente abaixo do esperado:
            </div>
            <ul>
        """)
        for vm in resultado.abaixo_tempo:
            html_parts.append(f'<li><span class="name">{vm.nome}</span> – <span class="value">{_fmt_tempo(vm.valor)}</span></li>')
        html_parts.append("</ul></div>")

    # 5. Visitas não realizadas
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

    # 6. Somente remotas
    if resultado.somente_remota:
        html_parts.append("""
        <div class="section">
            <div class="section-title text-orange">
                <span class="icon">⚠️</span> Ponto de atenção — realizaram visitas apenas de forma remota:
            </div>
            <ul>
        """)
        for nome in resultado.somente_remota:
            html_parts.append(f'<li><span class="name">{nome}</span></li>')
        html_parts.append("</ul></div>")

    # 7. Clientes atendidos remotamente acima da média
    if resultado.acima_visitas_rem:
        html_parts.append(f"""
        <div class="section">
            <div class="section-title text-teal">
                <span class="icon">📞</span> Clientes atendidos remotamente acima da média do time ({resultado.media_visitas_rem}):
            </div>
            <ul>
        """)
        for vr in resultado.acima_visitas_rem:
            html_parts.append(f'<li><span class="name">{vr.nome}</span> – <span class="value">{vr.visitas_rem}</span> atendimentos remotas (de {vr.visitas_prev} planejadas)</li>')
        html_parts.append("</ul></div>")

    # Aviso fixo
    html_parts.append("""
        <div class="footer">
            <span class="icon">⚠️</span> Reforçamos que visitas remotas não são consideradas no cálculo da aderência à rota.
        </div>
    </div>
    """)

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

    # Renderiza com html2image. Se estiver rodando em ambiente sem Chrome (ex: Streamlit Cloud),
    # o html2image/pyppeteer pode falhar; neste caso caímos em um fallback simples usando Pillow
    # para gerar uma imagem textual (garante que a app não quebre).
    hti = Html2Image(size=(800, 1000))

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            hti.output_path = tmpdirname
            filename = "relatorio.png"
            # Gera o PNG a partir da string HTML
            hti.screenshot(html_str=html_content, save_as=filename)
            # Lê os bytes gerados
            filepath = os.path.join(tmpdirname, filename)
            with open(filepath, "rb") as f:
                return f.read()

    except Exception as e:
        # Fallback: gerar imagem simples com texto (remove tags HTML e emojis)
        import re
        from io import BytesIO
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            # Se Pillow não estiver disponível por algum motivo, re-raise a exceção original
            raise

        def _strip_emoji(text: str) -> str:
            return "".join(ch for ch in text if ord(ch) <= 0xFFFF)

        # Remove tags HTML e compacta espaços
        text = re.sub(r"<[^>]+>", "", html_content)
        text = re.sub(r"\s+", " ", text).strip()

        # Cria imagem básica
        width = 800
        font = ImageFont.load_default()
        # calcula altura aproximada
        lines = []
        max_chars_per_line = 90
        for i in range(0, len(text), max_chars_per_line):
            lines.append(_strip_emoji(text[i:i+max_chars_per_line]))

        line_height = font.getsize("A")[1] + 4
        height = max(600, line_height * len(lines) + 40)

        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)
        x, y = 20, 20
        fill = (30, 41, 59)
        for line in lines:
            if not line:
                y += line_height
                continue
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height

        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
