# loader.py
# Responsável por carregar e normalizar a planilha de visitas.

from __future__ import annotations

import re
from datetime import time
from pathlib import Path

import pandas as pd

from config import COLUNAS


# ---------------------------------------------------------------------------
# Helpers de conversão
# ---------------------------------------------------------------------------

def _parse_percent(value: object) -> float | None:
    """Converte '60%' ou 0.6 ou 60 para float 60.0 (sempre em escala 0-100)."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        # Se já vier como decimal (0 a 1), converte para 0-100
        v = float(value)
        return round(v * 100, 2) if v <= 1.0 else round(v, 2)
    s = str(value).strip().replace(",", ".").replace("%", "")
    try:
        v = float(s)
        return round(v * 100, 2) if v <= 1.0 else round(v, 2)
    except ValueError:
        return None


def _parse_time(value: object) -> time | None:
    """Converte '11:46' ou datetime/time para datetime.time."""
    if pd.isna(value):
        return None
    if isinstance(value, time):
        return value
    if hasattr(value, "time"):          # datetime or Timestamp
        return value.time()             # type: ignore[union-attr]
    s = str(value).strip()
    # Aceita HH:MM ou HH:MM:SS
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    if m:
        h, mi, se = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        try:
            return time(h, mi, se)
        except ValueError:
            # Valores como "24:00" ou "09:99" têm formato válido, mas
            # não representam um horário. Tratamos como dado ausente para
            # que a planilha continue sendo analisada sem encerrar a aplicação.
            return None
    return None


def _time_to_minutes(t: time | None) -> float | None:
    """Transforma datetime.time em minutos totais desde meia-noite."""
    if t is None:
        return None
    return t.hour * 60 + t.minute + t.second / 60


def _minutes_to_time(minutes: float) -> str:
    """Converte minutos totais para string 'HH:MM'."""
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h:02d}:{m:02d}"


def formatar_nome_vendedor(nome: object) -> str:
    """Retorna apenas o primeiro nome e o último sobrenome."""
    if pd.isna(nome):
        return ""
    partes = str(nome).strip().split()
    if not partes:
        return ""
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[-1]}"


# ---------------------------------------------------------------------------
# Carregamento principal
# ---------------------------------------------------------------------------

def load(filepath: str | Path | object, sheet: int | str = 0) -> pd.DataFrame:
    """
    Carrega a planilha e retorna um DataFrame limpo com colunas padronizadas.

    Parâmetros
    ----------
    filepath : caminho para o arquivo .xlsx ou .csv, ou um objeto de arquivo (ex: UploadedFile do Streamlit)
    sheet    : índice ou nome da aba (ignorado para CSV)

    Retorna
    -------
    DataFrame com as colunas internas definidas em config.COLUNAS.
    """
    is_file_like = hasattr(filepath, "read")
    
    if is_file_like:
        # Objeto de arquivo em memória (ex: do Streamlit)
        filename = getattr(filepath, "name", "")
        if filename.lower().endswith((".xlsx", ".xls", ".xlsm")):
            raw = pd.read_excel(filepath, sheet_name=sheet, dtype=str)
        elif filename.lower().endswith(".csv"):
            raw = pd.read_csv(filepath, dtype=str, sep=None, engine="python")
        else:
            raise ValueError(f"Formato não suportado para o arquivo: {filename}")
    else:
        # Caminho tradicional no sistema de arquivos
        path = Path(str(filepath))
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        if path.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
            raw = pd.read_excel(path, sheet_name=sheet, dtype=str)
        elif path.suffix.lower() == ".csv":
            raw = pd.read_csv(path, dtype=str, sep=None, engine="python")
        else:
            raise ValueError(f"Formato não suportado: {path.suffix}")

    # --- Normaliza nomes de colunas (strip de espaços) ---
    raw.columns = [str(c).strip() for c in raw.columns]

    # --- Verifica colunas obrigatórias ---
    expected = set(COLUNAS.values())
    missing = expected - set(raw.columns)
    if missing:
        raise ValueError(
            f"Colunas não encontradas na planilha:\n  " +
            "\n  ".join(sorted(missing)) +
            f"\n\nColunas disponíveis:\n  " +
            "\n  ".join(sorted(raw.columns))
        )

    # --- Seleciona e renomeia para nomes internos ---
    inv = {v: k for k, v in COLUNAS.items()}
    df = raw[list(COLUNAS.values())].rename(columns=inv).copy()

    # --- Limpeza de strings ---
    df["vendedor"] = df["vendedor"].apply(formatar_nome_vendedor)
    df["gestor"] = df["gestor"].str.strip()

    # --- Converte numéricos inteiros ---
    for col in ("qtde_clientes", "visitas_prev", "visitas_real",
                "visitas_pres", "visitas_rem", "visitas_nao"):
        df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").fillna(0).astype(int)

    # --- Converte % aderência ---
    df["aderencia"] = df["aderencia"].apply(_parse_percent)

    # --- Converte horários ---
    df["checkin_time"] = df["checkin"].apply(_parse_time)
    df["checkout_time"] = df["checkout"].apply(_parse_time)
    df["checkin_min"] = df["checkin_time"].apply(_time_to_minutes)
    df["checkout_min"] = df["checkout_time"].apply(_time_to_minutes)

    # --- Tempo no cliente (em minutos) ---
    df["tempo_min"] = pd.to_numeric(
        df["tempo_cliente"].str.replace(",", "."), errors="coerce"
    )

    # Remove linhas sem vendedor
    df = df[df["vendedor"].notna() & (df["vendedor"] != "")].reset_index(drop=True)

    return df


def minutes_to_time_str(minutes: float) -> str:
    """Exporta a função de conversão para uso em outros módulos."""
    return _minutes_to_time(minutes)
