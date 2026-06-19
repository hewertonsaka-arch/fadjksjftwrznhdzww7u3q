# analyzer.py
# Calcula todas as métricas de equipe e retorna estrutura de dados para o formatter.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from config import TEMPO_MINIMO_CLIENTE_MIN
from loader import minutes_to_time_str


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

@dataclass
class VendedorMetrica:
    nome: str
    valor: float | int | str


@dataclass
class VendedorVisitasRemotas:
    nome: str
    visitas_rem: int
    visitas_prev: int


@dataclass
class VendedorRankingAderencia:
    nome: str
    aderencia: float


@dataclass
class VendedorComparativo:
    nome: str
    visitas_pres: int
    visitas_rem: int
    visitas_nao: int
    visitas_prev: int


@dataclass
class ResultadoAnalise:
    periodo: str
    gestor_selecionado: str | None = None

    # Aderência à rota
    media_aderencia: float = 0.0
    abaixo_aderencia: list[VendedorMetrica] = field(default_factory=list)
    acima_aderencia: list[VendedorMetrica] = field(default_factory=list)   # NOVO: positivos

    # Check-in
    media_checkin_min: float = 0.0          # em minutos totais
    acima_checkin: list[VendedorMetrica] = field(default_factory=list)
    abaixo_checkin: list[VendedorMetrica] = field(default_factory=list)    # NOVO: pontuais

    # Check-out
    media_checkout_min: float = 0.0         # em minutos totais
    abaixo_checkout: list[VendedorMetrica] = field(default_factory=list)
    acima_checkout: list[VendedorMetrica] = field(default_factory=list)    # NOVO: ficam mais tarde

    # Tempo no cliente
    media_tempo_min: float = 0.0            # em minutos
    limiar_tempo: float = 0.0              # limiar efetivo usado
    abaixo_tempo: list[VendedorMetrica] = field(default_factory=list)
    acima_tempo: list[VendedorMetrica] = field(default_factory=list)       # NOVO: positivos

    # Visitas não realizadas
    nao_realizadas: list[VendedorMetrica] = field(default_factory=list)
    sem_faltas: list[str] = field(default_factory=list)                    # NOVO: zero faltas

    # Vendedores com visitas SOMENTE remotas (ponto de atenção)
    somente_remota: list[str] = field(default_factory=list)

    # Visitas remotas acima da média
    media_visitas_rem: float = 0.0
    acima_visitas_rem: list[VendedorVisitasRemotas] = field(default_factory=list)

    # Gestores presentes (para info extra)
    gestores: list[str] = field(default_factory=list)

    # NOVO: campos para Análise Criteriosa
    total_vendedores: int = 0
    ranking_aderencia: list[VendedorRankingAderencia] = field(default_factory=list)
    ranking_nao_realizadas: list[VendedorMetrica] = field(default_factory=list)
    comparativo_pres_rem: list[VendedorComparativo] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def analisar(df: pd.DataFrame, periodo: str, gestor: Optional[str] = None) -> ResultadoAnalise:
    """
    Realiza toda a análise sobre o DataFrame carregado.

    Parâmetros
    ----------
    df      : DataFrame limpo retornado por loader.load()
    periodo : string descritiva do período (ex: "01 a 12/06")
    gestor  : se informado, filtra a base por este gestor

    Retorna
    -------
    ResultadoAnalise com todas as métricas calculadas.
    """
    if gestor:
        df = df[df["gestor"].str.lower() == gestor.lower()].copy()
        if df.empty:
            raise ValueError(f"Nenhum registro encontrado para o gestor: '{gestor}'")

    resultado = ResultadoAnalise(periodo=periodo, gestor_selecionado=gestor)
    resultado.gestores = sorted(df["gestor"].dropna().unique().tolist())

    # -----------------------------------------------------------------------
    # 1. Aderência à rota
    # -----------------------------------------------------------------------
    df_ad = df[df["aderencia"].notna()].copy()
    if not df_ad.empty:
        media_ad = df_ad["aderencia"].mean()
        resultado.media_aderencia = round(media_ad, 1)
        abaixo = df_ad[df_ad["aderencia"] < media_ad].sort_values("aderencia")
        resultado.abaixo_aderencia = [
            VendedorMetrica(nome=row["vendedor"], valor=round(row["aderencia"], 0))
            for _, row in abaixo.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 2. Check-in — acima da média (entram mais tarde = número maior)
    # -----------------------------------------------------------------------
    df_ci = df[df["checkin_min"].notna()].copy()
    if not df_ci.empty:
        media_ci = df_ci["checkin_min"].mean()
        resultado.media_checkin_min = media_ci
        acima = df_ci[df_ci["checkin_min"] > media_ci].sort_values("checkin_min", ascending=False)
        resultado.acima_checkin = [
            VendedorMetrica(nome=row["vendedor"], valor=minutes_to_time_str(row["checkin_min"]))
            for _, row in acima.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 3. Check-out — abaixo da média (saem mais cedo = número menor)
    # -----------------------------------------------------------------------
    df_co = df[df["checkout_min"].notna()].copy()
    if not df_co.empty:
        media_co = df_co["checkout_min"].mean()
        resultado.media_checkout_min = media_co
        abaixo_co = df_co[df_co["checkout_min"] < media_co].sort_values("checkout_min")
        resultado.abaixo_checkout = [
            VendedorMetrica(nome=row["vendedor"], valor=minutes_to_time_str(row["checkout_min"]))
            for _, row in abaixo_co.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 4. Tempo no cliente — abaixo do limiar
    # -----------------------------------------------------------------------
    df_tp = df[df["tempo_min"].notna()].copy()
    if not df_tp.empty:
        media_tp = df_tp["tempo_min"].mean()
        resultado.media_tempo_min = round(media_tp, 1)

        # Usa o limiar configurado ou a média da equipe
        limiar = TEMPO_MINIMO_CLIENTE_MIN if TEMPO_MINIMO_CLIENTE_MIN is not None else media_tp
        resultado.limiar_tempo = round(limiar, 1)

        abaixo_tp = df_tp[df_tp["tempo_min"] < limiar].sort_values("tempo_min")
        resultado.abaixo_tempo = [
            VendedorMetrica(nome=row["vendedor"], valor=int(round(row["tempo_min"])))
            for _, row in abaixo_tp.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 5. Visitas não realizadas
    # -----------------------------------------------------------------------
    df_nr = df[df["visitas_nao"] > 0].copy()
    if not df_nr.empty:
        df_nr = df_nr.sort_values("visitas_nao", ascending=False)
        resultado.nao_realizadas = [
            VendedorMetrica(nome=row["vendedor"], valor=int(row["visitas_nao"]))
            for _, row in df_nr.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 6. Vendedores somente com visitas remotas (ponto de atenção)
    # -----------------------------------------------------------------------
    mask_somente_rem = (
        (df["visitas_rem"] > 0) &
        (df["visitas_pres"] == 0) &
        (df["visitas_nao"] == 0)
    )
    resultado.somente_remota = df[mask_somente_rem]["vendedor"].tolist()

    # -----------------------------------------------------------------------
    # 7. Clientes atendidos remotamente acima da média
    # -----------------------------------------------------------------------
    df_rem = df[df["visitas_rem"].notna()].copy()
    if not df_rem.empty:
        media_rem = df_rem["visitas_rem"].mean()
        resultado.media_visitas_rem = round(media_rem, 1)
        acima_rem = df_rem[df_rem["visitas_rem"] > media_rem].sort_values("visitas_rem", ascending=False)
        resultado.acima_visitas_rem = [
            VendedorVisitasRemotas(
                nome=row["vendedor"],
                visitas_rem=int(row["visitas_rem"]),
                visitas_prev=int(row["visitas_prev"])
            )
            for _, row in acima_rem.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 8. Positivos de aderência (acima da média)
    # -----------------------------------------------------------------------
    if not df_ad.empty:
        acima_ad = df_ad[df_ad["aderencia"] >= media_ad].sort_values("aderencia", ascending=False)
        resultado.acima_aderencia = [
            VendedorMetrica(nome=row["vendedor"], valor=round(row["aderencia"], 0))
            for _, row in acima_ad.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 9. Check-in pontual (abaixo da média = entra mais cedo)
    # -----------------------------------------------------------------------
    if not df_ci.empty:
        abaixo_ci = df_ci[df_ci["checkin_min"] <= media_ci].sort_values("checkin_min")
        resultado.abaixo_checkin = [
            VendedorMetrica(nome=row["vendedor"], valor=minutes_to_time_str(row["checkin_min"]))
            for _, row in abaixo_ci.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 10. Check-out positivo (acima da média = fica mais tarde)
    # -----------------------------------------------------------------------
    if not df_co.empty:
        acima_co = df_co[df_co["checkout_min"] >= media_co].sort_values("checkout_min", ascending=False)
        resultado.acima_checkout = [
            VendedorMetrica(nome=row["vendedor"], valor=minutes_to_time_str(row["checkout_min"]))
            for _, row in acima_co.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 11. Tempo no cliente positivo (acima do limiar)
    # -----------------------------------------------------------------------
    if not df_tp.empty:
        acima_tp = df_tp[df_tp["tempo_min"] >= limiar].sort_values("tempo_min", ascending=False)
        resultado.acima_tempo = [
            VendedorMetrica(nome=row["vendedor"], valor=int(round(row["tempo_min"])))
            for _, row in acima_tp.iterrows()
        ]

    # -----------------------------------------------------------------------
    # 12. Sem faltas (visitas_nao == 0)
    # -----------------------------------------------------------------------
    resultado.sem_faltas = df[df["visitas_nao"] == 0]["vendedor"].tolist()

    # -----------------------------------------------------------------------
    # 13. Total de vendedores
    # -----------------------------------------------------------------------
    resultado.total_vendedores = len(df)

    # -----------------------------------------------------------------------
    # 14. Ranking completo de aderência
    # -----------------------------------------------------------------------
    df_rank = df[df["aderencia"].notna()].sort_values("aderencia", ascending=False)
    resultado.ranking_aderencia = [
        VendedorRankingAderencia(nome=row["vendedor"], aderencia=round(row["aderencia"], 1))
        for _, row in df_rank.iterrows()
    ]

    # -----------------------------------------------------------------------
    # 15. Ranking de visitas não realizadas (todos, incluindo zeros)
    # -----------------------------------------------------------------------
    df_nr_all = df.sort_values("visitas_nao", ascending=False)
    resultado.ranking_nao_realizadas = [
        VendedorMetrica(nome=row["vendedor"], valor=int(row["visitas_nao"]))
        for _, row in df_nr_all.iterrows()
    ]

    # -----------------------------------------------------------------------
    # 16. Comparativo presencial vs. remoto por vendedor
    # -----------------------------------------------------------------------
    resultado.comparativo_pres_rem = [
        VendedorComparativo(
            nome=row["vendedor"],
            visitas_pres=int(row["visitas_pres"]),
            visitas_rem=int(row["visitas_rem"]),
            visitas_nao=int(row["visitas_nao"]),
            visitas_prev=int(row["visitas_prev"]),
        )
        for _, row in df.iterrows()
    ]

    return resultado
