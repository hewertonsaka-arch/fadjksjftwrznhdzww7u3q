# formatter.py
# Gera o texto de resumo formatado com emojis, pronto para compartilhamento.

from __future__ import annotations

from analyzer import ResultadoAnalise
from loader import minutes_to_time_str


def _fmt_aderencia(v: float) -> str:
    return f"{int(v)}%"


def _fmt_tempo(v: int | float) -> str:
    return f"{int(v)}min"


def gerar_resumo(resultado: ResultadoAnalise) -> str:
    """
    Gera a string de resumo completa a partir de um ResultadoAnalise
    conforme o novo padrão definido:
    - Cabeçalho com coordenador e período
    - Check-in acima da média do time [hora]
    - Check-out abaixo da média do time [hora]
    - Visitas não realizadas
    """
    linhas: list[str] = []

    # --- Cabeçalho ---
    nome_gestor = resultado.gestor_selecionado if resultado.gestor_selecionado else "Geral"
    linhas.append(f"Resumo de Visitas {nome_gestor}")
    linhas.append(f"Período apurado: {resultado.periodo}")
    linhas.append("")
    linhas.append("")

    # --- 1. Check-in acima da média ---
    if resultado.acima_checkin:
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        linhas.append(f"📤 Check-in acima da média do time [{media_ci_str}]:")
        for vm in resultado.acima_checkin:
            linhas.append(f"* {vm.nome} – {vm.valor}")
        linhas.append("")

    # --- 2. Check-out abaixo da média ---
    if resultado.abaixo_checkout:
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        linhas.append(f"📥 Check-out abaixo da média do time [{media_co_str}]:")
        for vm in resultado.abaixo_checkout:
            linhas.append(f"* {vm.nome} – {vm.valor}")
        linhas.append("")
        linhas.append("")

    # --- 3. Visitas não realizadas ---
    if resultado.nao_realizadas:
        linhas.append("❌ Visitas não realizadas:")
        for vm in resultado.nao_realizadas:
            linhas.append(f"* {vm.nome}  – {vm.valor}")

    return "\n".join(linhas)
