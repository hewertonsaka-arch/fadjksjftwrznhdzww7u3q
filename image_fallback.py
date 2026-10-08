"""Renderiza relatórios em PNG quando o navegador HTML não está disponível."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, *, bold: bool = False):
    candidates = (
        (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf")
        if bold
        else (r"C:\Windows\Fonts\arial.ttf",)
    ) + (("DejaVuSans-Bold.ttf",) if bold else ("DejaVuSans.ttf",))

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def gerar_imagem_fallback(
    titulo: str,
    periodo: str,
    secoes: list[tuple[str, list[str]]],
    *,
    tema_escuro: bool = False,
) -> bytes:
    """Gera um relatório organizado usando Pillow, sem depender de HTML/Chrome."""
    largura = 1000
    margem = 48
    largura_texto = largura - margem * 2 - 48
    fonte_titulo = _load_font(28, bold=True)
    fonte_periodo = _load_font(17)
    fonte_secao = _load_font(19, bold=True)
    fonte_item = _load_font(17)
    altura_linha = 27

    fundo = (15, 23, 42) if tema_escuro else (241, 245, 249)
    texto = (226, 232, 240) if tema_escuro else (30, 41, 59)
    secundario = (148, 163, 184) if tema_escuro else (100, 116, 139)
    cartao = (30, 41, 59) if tema_escuro else (255, 255, 255)
    borda = (51, 65, 85) if tema_escuro else (226, 232, 240)
    azul = (59, 130, 246)

    # Mede e quebra cada item por largura real, mantendo nomes e valores juntos.
    medidor = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def quebrar_linha(valor: str, fonte) -> list[str]:
        palavras = valor.split()
        linhas: list[str] = []
        atual = ""
        for palavra in palavras:
            teste = f"{atual} {palavra}".strip()
            if atual and medidor.textlength(teste, font=fonte) > largura_texto:
                linhas.append(atual)
                atual = palavra
            else:
                atual = teste
        if atual:
            linhas.append(atual)
        return linhas or [""]

    layout: list[tuple[str, list[list[str]]]] = []
    altura = margem + 50 + 38 + 28
    for nome_secao, itens in secoes:
        linhas_itens = [quebrar_linha(item, fonte_item) for item in itens]
        layout.append((nome_secao, linhas_itens))
        altura += 24 + 18 + sum(max(1, len(linhas)) * altura_linha for linhas in linhas_itens)
        altura += 24
    altura = max(300, altura + margem)

    imagem = Image.new("RGB", (largura, altura), fundo)
    draw = ImageDraw.Draw(imagem)
    draw.rounded_rectangle(
        (margem, margem, largura - margem, altura - margem),
        radius=18,
        fill=cartao,
        outline=borda,
        width=2,
    )

    x = margem + 30
    y = margem + 28
    draw.rounded_rectangle((x, y, x + 8, y + 82), radius=4, fill=azul)
    draw.text((x + 24, y), titulo, font=fonte_titulo, fill=texto)
    draw.text((x + 24, y + 45), f"Período apurado: {periodo}", font=fonte_periodo, fill=secundario)
    y += 108

    for nome_secao, linhas_itens in layout:
        if y > margem + 120:
            y += 8
        draw.text((x, y), nome_secao, font=fonte_secao, fill=azul)
        y += 34
        if not linhas_itens:
            draw.text((x + 8, y), "Nenhum registro neste período.", font=fonte_item, fill=secundario)
            y += altura_linha
        for linhas in linhas_itens:
            draw.ellipse((x + 8, y + 9, x + 16, y + 17), fill=azul)
            for indice, linha in enumerate(linhas):
                draw.text((x + 28, y), linha, font=fonte_item, fill=texto)
                y += altura_linha

    buffer = BytesIO()
    imagem.save(buffer, format="PNG")
    return buffer.getvalue()
