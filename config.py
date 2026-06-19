# config.py
# Configurações centrais do Rote Assist

# ---------------------------------------------------------------------------
# Mapeamento de colunas esperadas na planilha
# Chave = nome interno usado no código | Valor = nome (ou variações) na planilha
# ---------------------------------------------------------------------------
COLUNAS = {
    "gestor":         "Gestor Atualizado",
    "vendedor":       "Nome Vendedor",
    "qtde_clientes":  "Qtde Clientes",
    "visitas_prev":   "Qtde Visitas no Periodo (Atual)",
    "visitas_real":   "Qtde Visita Realizada",
    "visitas_pres":   "Qtde Visita Presencial",
    "visitas_rem":    "Qtde Visita Remota",
    "visitas_nao":    "Qtde Visita Não Realizada",
    "aderencia":      "% Aderencia de Rota",
    "checkin":        "Média Horário Check-in",
    "checkout":       "Média Horário Check-out",
    "tempo_cliente":  "Média de Tempo no Cliente <60",
}

# ---------------------------------------------------------------------------
# Regras de negócio
# ---------------------------------------------------------------------------

# Tempo mínimo (minutos) de permanência considerado adequado.
# Se None, usa a média da equipe como limiar.
TEMPO_MINIMO_CLIENTE_MIN: int | None = None

# Se True, gera relatório separado por gestor quando há mais de um na base.
FILTRAR_POR_GESTOR: bool = True

# ---------------------------------------------------------------------------
# Formatação de saída
# ---------------------------------------------------------------------------

# Salvar automaticamente o resumo em arquivo .txt após gerar?
SALVAR_TXT_AUTO: bool = False

# Tentar copiar para área de transferência automaticamente?
COPIAR_CLIPBOARD_AUTO: bool = False

# Formato do cabeçalho do período (usado quando o usuário digita manualmente)
# Exemplo: "01 a 12/06"
FORMATO_PERIODO_EXEMPLO: str = "01 a 12/06"
