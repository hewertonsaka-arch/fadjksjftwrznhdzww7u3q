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
    Gera a string de resumo completa a partir de um ResultadoAnalise.

    Retorna a string formatada (pronta para print ou salvar em arquivo).
    """
    linhas: list[str] = []

    # --- Cabeçalho ---
    nome_gestor = resultado.gestor_selecionado if resultado.gestor_selecionado else "Geral"
    linhas.append(f"Resumo de Visitas {nome_gestor}")
    linhas.append(f"Período apurado: {resultado.periodo}")
    linhas.append("")

    # --- 1. Aderência à rota ---
    if resultado.abaixo_aderencia:
        media_str = _fmt_aderencia(resultado.media_aderencia)
        linhas.append(f"🔻 Aderência à rota abaixo da média da equipe ({media_str}):")
        for vm in resultado.abaixo_aderencia:
            linhas.append(f"* {vm.nome} – {_fmt_aderencia(vm.valor)}")
        linhas.append("")
    else:
        linhas.append(
            f"✅ Todos os vendedores estão acima ou na média de aderência à rota "
            f"({_fmt_aderencia(resultado.media_aderencia)})."
        )
        linhas.append("")

    # --- 2. Check-in acima da média ---
    if resultado.acima_checkin:
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        linhas.append(f"📤 Check-in acima da média do time ({media_ci_str}):")
        for vm in resultado.acima_checkin:
            linhas.append(f"* {vm.nome} – {vm.valor}")
        linhas.append("")

    # --- 3. Check-out abaixo da média ---
    if resultado.abaixo_checkout:
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        linhas.append(f"📥 Check-out abaixo da média do time ({media_co_str}):")
        for vm in resultado.abaixo_checkout:
            linhas.append(f"* {vm.nome} – {vm.valor}")
        linhas.append("")

    # --- 4. Tempo no cliente ---
    if resultado.abaixo_tempo:
        linhas.append(
            "⏳ Além disso, alguns colaboradores apresentaram tempo médio de "
            "permanência no cliente abaixo do esperado:"
        )
        for vm in resultado.abaixo_tempo:
            linhas.append(f"* {vm.nome} – {_fmt_tempo(vm.valor)}")
        linhas.append("")

    # --- 5. Visitas não realizadas ---
    if resultado.nao_realizadas:
        linhas.append("❌ Visitas não realizadas:")
        for vm in resultado.nao_realizadas:
            linhas.append(f"* {vm.nome}  – {vm.valor}")
        linhas.append("")

    # --- 6. Ponto de atenção: somente visitas remotas ---
    if resultado.somente_remota:
        linhas.append("⚠️ Ponto de atenção — realizaram visitas apenas de forma remota:")
        for nome in resultado.somente_remota:
            linhas.append(f"* {nome}")
        linhas.append("")

    # --- 7. Clientes atendidos remotamente acima da média ---
    if resultado.acima_visitas_rem:
        linhas.append(f"📞 Clientes atendidos remotamente acima da média do time ({resultado.media_visitas_rem}):")
        for vr in resultado.acima_visitas_rem:
            linhas.append(f"* {vr.nome} – {vr.visitas_rem} visitas remotas (de {vr.visitas_prev} planejadas)")
        linhas.append("")

    # --- Aviso fixo ---
    linhas.append(
        "⚠️ Reforçamos que visitas remotas não são consideradas no cálculo "
        "da aderência à rota."
    )

    return "\n".join(linhas)
