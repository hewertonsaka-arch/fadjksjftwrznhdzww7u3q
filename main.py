# main.py
# CLI interativo do Rote Assist.

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from rich.text import Text

import loader
import analyzer
import formatter
from config import FORMATO_PERIODO_EXEMPLO

console = Console()


# ---------------------------------------------------------------------------
# Banner de abertura
# ---------------------------------------------------------------------------

def _banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]📊 Rote Assist[/bold cyan]\n"
            "[dim]Gera resumos automáticos prontos para compartilhamento[/dim]",
            border_style="cyan",
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Solicita o arquivo
# ---------------------------------------------------------------------------

def _pedir_arquivo() -> Path:
    while True:
        caminho = Prompt.ask(
            "[bold yellow]📂 Caminho da planilha[/bold yellow] "
            "[dim](.xlsx ou .csv)[/dim]"
        ).strip().strip('"').strip("'")
        path = Path(caminho)
        if path.exists():
            return path
        console.print(f"[red]❌ Arquivo não encontrado:[/red] {path}")


# ---------------------------------------------------------------------------
# Solicita o período
# ---------------------------------------------------------------------------

def _pedir_periodo() -> str:
    console.print(
        f"[dim]Exemplo de formato: [bold]{FORMATO_PERIODO_EXEMPLO}[/bold][/dim]"
    )
    return Prompt.ask("[bold yellow]📅 Período do relatório[/bold yellow]").strip()


# ---------------------------------------------------------------------------
# Exibe tabela de resumo no terminal (dados brutos)
# ---------------------------------------------------------------------------

def _exibir_tabela(df) -> None:
    table = Table(
        title="📋 Dados carregados",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Vendedor", style="cyan", no_wrap=True)
    table.add_column("Coordenador", style="dim")
    table.add_column("Aderência", justify="right")
    table.add_column("Check-in", justify="right")
    table.add_column("Check-out", justify="right")
    table.add_column("Tempo (min)", justify="right")
    table.add_column("Não Realiz.", justify="right")

    for _, row in df.iterrows():
        ader = f"{int(row['aderencia'])}%" if row["aderencia"] is not None else "–"
        table.add_row(
            str(row["vendedor"]),
            str(row["gestor"]),
            ader,
            str(row["checkin"]) if row["checkin"] else "–",
            str(row["checkout"]) if row["checkout"] else "–",
            str(int(row["tempo_min"])) if row["tempo_min"] == row["tempo_min"] else "–",
            str(int(row["visitas_nao"])),
        )

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Seleção de coordenador (sempre solicitada)
# ---------------------------------------------------------------------------

def _pedir_gestor(gestores: list[str]) -> str | None:
    if len(gestores) == 0:
        return None

    if len(gestores) == 1:
        console.print(f"[dim]Coordenador detectado:[/dim] [cyan]{gestores[0]}[/cyan]\n")
        return gestores[0]

    console.print("[bold]Coordenadores encontrados na base:[/bold]")
    for i, g in enumerate(gestores, 1):
        console.print(f"  [cyan]{i}.[/cyan] {g}")
    console.print(f"  [cyan]{len(gestores)+1}.[/cyan] [dim]Todos (sem filtro)[/dim]")

    while True:
        escolha = Prompt.ask("\nSelecione o coordenador [bold](número)[/bold]").strip()
        if escolha.isdigit():
            idx = int(escolha) - 1
            if 0 <= idx < len(gestores):
                return gestores[idx]
            if idx == len(gestores):
                return None
        console.print("[red]Opção inválida. Tente novamente.[/red]")


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def main() -> None:
    _banner()

    # 1. Carregar arquivo
    path = _pedir_arquivo()
    console.print(f"[green]✔ Arquivo carregado:[/green] {path.name}\n")

    try:
        df = loader.load(path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red bold]Erro ao carregar a planilha:[/red bold]\n{e}")
        sys.exit(1)

    # 2. Pré-visualização da tabela
    _exibir_tabela(df)

    # 3. Seleção de coordenador
    gestores_disponiveis = sorted(df["gestor"].dropna().unique().tolist())
    gestor_filtro = _pedir_gestor(gestores_disponiveis)
    console.print()

    # 4. Período
    periodo = _pedir_periodo()
    console.print()

    # 5. Análise
    with console.status("[bold cyan]Analisando dados...[/bold cyan]"):
        try:
            resultado = analyzer.analisar(df, periodo, gestor=gestor_filtro)
        except ValueError as e:
            console.print(f"[red bold]Erro na análise:[/red bold] {e}")
            sys.exit(1)

    # 6. Gerar e exibir resumo no terminal
    resumo = formatter.gerar_resumo(resultado)

    console.print(
        Panel(
            Text(resumo),
            title="[bold green]✅ Resumo gerado[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )

    console.print("\n[dim]Obrigado por usar o Rote Assist. Até logo![/dim]\n")


if __name__ == "__main__":
    main()
