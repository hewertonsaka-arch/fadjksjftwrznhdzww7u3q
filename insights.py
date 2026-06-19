# insights.py
# Gera insights automáticos para tomada de decisão a partir do ResultadoAnalise.

from __future__ import annotations

from analyzer import ResultadoAnalise
from loader import minutes_to_time_str


def gerar_insights(resultado: ResultadoAnalise) -> list[dict]:
    """
    Analisa o ResultadoAnalise e retorna uma lista de insights.

    Cada insight é um dict com:
        - tipo   : "positivo" | "negativo" | "atencao" | "neutro"
        - icone  : emoji representativo
        - titulo : frase curta de destaque
        - detalhe: texto explicativo para tomada de decisão
    """
    insights: list[dict] = []
    total = resultado.total_vendedores
    if total == 0:
        return insights

    # -----------------------------------------------------------------------
    # Aderência à rota
    # -----------------------------------------------------------------------
    n_abaixo_ad = len(resultado.abaixo_aderencia)
    n_acima_ad  = len(resultado.acima_aderencia)

    if n_abaixo_ad == 0:
        insights.append({
            "tipo": "positivo",
            "icone": "🏆",
            "titulo": "Equipe 100% acima da meta de aderência",
            "detalhe": (
                f"Todos os {total} vendedores atingiram ou superaram a média de aderência "
                f"à rota ({int(resultado.media_aderencia)}%). Excelente disciplina operacional."
            ),
        })
    else:
        pct = round(n_abaixo_ad / total * 100)
        insights.append({
            "tipo": "negativo",
            "icone": "📉",
            "titulo": f"{pct}% da equipe está abaixo da média de aderência à rota",
            "detalhe": (
                f"{n_abaixo_ad} de {total} vendedores ficaram abaixo da média da equipe "
                f"({int(resultado.media_aderencia)}%). "
                "Recomenda-se revisão das rotas ou conversa individual de alinhamento."
            ),
        })

    # Spread de aderência (diferença entre o melhor e o pior)
    if len(resultado.ranking_aderencia) >= 2:
        melhor = resultado.ranking_aderencia[0]
        pior   = resultado.ranking_aderencia[-1]
        spread = melhor.aderencia - pior.aderencia
        if spread >= 30:
            insights.append({
                "tipo": "atencao",
                "icone": "↔️",
                "titulo": f"Grande variação de aderência entre vendedores ({int(spread)} p.p.)",
                "detalhe": (
                    f"{melhor.nome} lidera com {int(melhor.aderencia)}% enquanto "
                    f"{pior.nome} registrou {int(pior.aderencia)}%. "
                    "Uma diferença acima de 30 p.p. pode indicar rotas desiguais ou falta de acompanhamento."
                ),
            })

    # -----------------------------------------------------------------------
    # Check-in
    # -----------------------------------------------------------------------
    n_atrasados = len(resultado.acima_checkin)
    if n_atrasados > 0:
        pct_ci = round(n_atrasados / total * 100)
        media_str = minutes_to_time_str(resultado.media_checkin_min)
        insights.append({
            "tipo": "negativo" if pct_ci >= 40 else "atencao",
            "icone": "⏰",
            "titulo": f"{n_atrasados} vendedor(es) com check-in tardio ({pct_ci}% da equipe)",
            "detalhe": (
                f"A média de check-in da equipe é {media_str}. "
                f"{n_atrasados} vendedor(es) entraram depois desse horário. "
                "Entradas tardias frequentes podem impactar o cumprimento das rotas."
            ),
        })
    else:
        insights.append({
            "tipo": "positivo",
            "icone": "✅",
            "titulo": "Toda a equipe fez check-in no horário ou antes da média",
            "detalhe": "Boa pontualidade no início das atividades de campo.",
        })

    # -----------------------------------------------------------------------
    # Check-out
    # -----------------------------------------------------------------------
    n_cedo = len(resultado.abaixo_checkout)
    if n_cedo > 0:
        pct_co = round(n_cedo / total * 100)
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        insights.append({
            "tipo": "negativo" if pct_co >= 40 else "atencao",
            "icone": "🚪",
            "titulo": f"{n_cedo} vendedor(es) com check-out antecipado ({pct_co}% da equipe)",
            "detalhe": (
                f"A média de check-out da equipe é {media_co_str}. "
                f"{n_cedo} vendedor(es) encerraram o dia antes desse horário. "
                "Saídas antecipadas recorrentes merecem investigação."
            ),
        })

    # -----------------------------------------------------------------------
    # Tempo no cliente
    # -----------------------------------------------------------------------
    n_curto = len(resultado.abaixo_tempo)
    if n_curto > 0:
        pct_tp = round(n_curto / total * 100)
        insights.append({
            "tipo": "negativo" if pct_tp >= 50 else "atencao",
            "icone": "⏳",
            "titulo": f"{n_curto} vendedor(es) com tempo insuficiente no cliente",
            "detalhe": (
                f"Tempo médio da equipe: {int(resultado.media_tempo_min)} min "
                f"(limiar: {int(resultado.limiar_tempo)} min). "
                f"{pct_tp}% da equipe ficou abaixo do esperado. "
                "Visitas curtas reduzem a qualidade do relacionamento com o cliente."
            ),
        })
    else:
        insights.append({
            "tipo": "positivo",
            "icone": "🕐",
            "titulo": "Equipe com bom tempo de permanência nos clientes",
            "detalhe": (
                f"Todos os vendedores ficaram acima do limiar de {int(resultado.limiar_tempo)} min. "
                "Isso é um bom indicador de qualidade das visitas."
            ),
        })

    # -----------------------------------------------------------------------
    # Visitas não realizadas
    # -----------------------------------------------------------------------
    n_com_faltas = len(resultado.nao_realizadas)
    n_sem_faltas = len(resultado.sem_faltas)
    total_nao = sum(int(vm.valor) for vm in resultado.nao_realizadas)

    if n_sem_faltas == total:
        insights.append({
            "tipo": "positivo",
            "icone": "🎯",
            "titulo": "Nenhum vendedor teve visita não realizada!",
            "detalhe": "Toda a equipe cumpriu 100% das visitas planejadas no período. Resultado excelente.",
        })
    elif n_com_faltas > 0:
        pct_nr = round(n_com_faltas / total * 100)
        # Concentração: top 3 representam quanto do total?
        top3_nao = sum(int(vm.valor) for vm in resultado.nao_realizadas[:3])
        pct_top3 = round(top3_nao / total_nao * 100) if total_nao > 0 else 0
        insights.append({
            "tipo": "negativo",
            "icone": "❌",
            "titulo": f"{n_com_faltas} vendedor(es) com visitas não realizadas ({total_nao} no total)",
            "detalhe": (
                f"{pct_nr}% da equipe deixou de realizar ao menos uma visita. "
                + (
                    f"Os 3 maiores concentram {pct_top3}% de todas as faltas — foco nesses casos pode gerar impacto rápido."
                    if n_com_faltas >= 3 else ""
                )
            ),
        })

    # -----------------------------------------------------------------------
    # Somente remotas (ponto crítico)
    # -----------------------------------------------------------------------
    n_remota = len(resultado.somente_remota)
    if n_remota > 0:
        insights.append({
            "tipo": "atencao",
            "icone": "⚠️",
            "titulo": f"{n_remota} vendedor(es) realizaram visitas APENAS remotamente",
            "detalhe": (
                "Vendedores sem nenhuma visita presencial representam um risco operacional. "
                "Visitas remotas não contam para aderência à rota e podem indicar falta de campo efetivo."
            ),
        })

    # -----------------------------------------------------------------------
    # Destaque positivo geral
    # -----------------------------------------------------------------------
    if resultado.ranking_aderencia:
        top = resultado.ranking_aderencia[0]
        insights.append({
            "tipo": "positivo",
            "icone": "🌟",
            "titulo": f"Melhor aderência: {top.nome} ({int(top.aderencia)}%)",
            "detalhe": "Referência positiva da equipe. Compartilhar as práticas deste vendedor pode elevar o time.",
        })

    return insights
