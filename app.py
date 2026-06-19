import streamlit as st
import pandas as pd
import os
from io import BytesIO

import loader
import analyzer
import formatter
import image_generator
import insights as insights_module
import analysis_image_generator
from config import FORMATO_PERIODO_EXEMPLO

# Configuração da página
st.set_page_config(page_title="Rote Assist", page_icon="📊", layout="centered")

# ---------------------------------------------------------------------------
# CSS global — tipografia e estilo dos cards da aba Análise
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Cards de pontos positivos / negativos / atenção */
.analise-card {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid transparent;
}
.card-verde    { background: #052e1622; border-color: #22c55e; }
.card-vermelho { background: #450a0a22; border-color: #ef4444; }
.card-amarelo  { background: #1c140022; border-color: #f59e0b; }

.card-title {
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 6px;
}
.card-list { margin: 0; padding-left: 16px; font-size: 13px; line-height: 1.7; }

/* Insight cards */
.insight-card {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid transparent;
}
.insight-positivo { background: #052e1622; border-color: #22c55e; }
.insight-negativo { background: #450a0a22; border-color: #ef4444; }
.insight-atencao  { background: #1c140022; border-color: #f59e0b; }
.insight-neutro   { background: #1e293b22; border-color: #64748b; }

.insight-titulo  { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.insight-detalhe { font-size: 13px; opacity: 0.8; line-height: 1.5; }

/* Seção header dentro da aba */
.section-header {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    opacity: 0.5;
    margin: 18px 0 8px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers de renderização
# ---------------------------------------------------------------------------

def _card(titulo: str, items: list[str], cor: str, icone: str) -> str:
    """Gera HTML de um card de ponto positivo/negativo."""
    lista = "".join(f"<li>{i}</li>" for i in items)
    return f"""
    <div class="analise-card card-{cor}">
        <div class="card-title">{icone} {titulo}</div>
        <ul class="card-list">{lista}</ul>
    </div>"""


def _insight_card(ins: dict) -> str:
    return f"""
    <div class="insight-card insight-{ins['tipo']}">
        <div class="insight-titulo">{ins['icone']} {ins['titulo']}</div>
        <div class="insight-detalhe">{ins['detalhe']}</div>
    </div>"""


def _render_pontos_positivos(resultado) -> None:
    """Renderiza todos os cards de pontos positivos."""
    from loader import minutes_to_time_str

    algum = False

    if resultado.acima_aderencia:
        algum = True
        items = [f"<b>{vm.nome}</b> — {int(vm.valor)}%" for vm in resultado.acima_aderencia]
        st.markdown(
            _card(
                f"Aderência acima da média da equipe ({int(resultado.media_aderencia)}%)",
                items, "verde", "✅"
            ),
            unsafe_allow_html=True,
        )

    if resultado.abaixo_checkin:
        algum = True
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.abaixo_checkin]
        st.markdown(
            _card(f"Check-in pontual (antes de {media_ci_str})", items, "verde", "⏰"),
            unsafe_allow_html=True,
        )

    if resultado.acima_checkout:
        algum = True
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.acima_checkout]
        st.markdown(
            _card(f"Check-out tardio positivo (depois de {media_co_str})", items, "verde", "🏁"),
            unsafe_allow_html=True,
        )

    if resultado.acima_tempo:
        algum = True
        items = [f"<b>{vm.nome}</b> — {int(vm.valor)} min" for vm in resultado.acima_tempo]
        st.markdown(
            _card(
                f"Bom tempo de permanência no cliente (≥ {int(resultado.limiar_tempo)} min)",
                items, "verde", "🕐"
            ),
            unsafe_allow_html=True,
        )

    if resultado.sem_faltas:
        algum = True
        items = [f"<b>{nome}</b>" for nome in resultado.sem_faltas]
        st.markdown(
            _card("Zero visitas não realizadas — cumpriram 100% das visitas", items, "verde", "🎯"),
            unsafe_allow_html=True,
        )

    if not algum:
        st.info("Nenhum ponto positivo de destaque identificado neste período.")


def _render_pontos_negativos(resultado) -> None:
    """Renderiza todos os cards de pontos negativos/atenção."""
    from loader import minutes_to_time_str

    algum = False

    if resultado.abaixo_aderencia:
        algum = True
        items = [f"<b>{vm.nome}</b> — {int(vm.valor)}%" for vm in resultado.abaixo_aderencia]
        st.markdown(
            _card(
                f"Aderência abaixo da média da equipe ({int(resultado.media_aderencia)}%)",
                items, "vermelho", "🔻"
            ),
            unsafe_allow_html=True,
        )

    if resultado.acima_checkin:
        algum = True
        media_ci_str = minutes_to_time_str(resultado.media_checkin_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.acima_checkin]
        st.markdown(
            _card(f"Check-in tardio (depois de {media_ci_str})", items, "vermelho", "📤"),
            unsafe_allow_html=True,
        )

    if resultado.abaixo_checkout:
        algum = True
        media_co_str = minutes_to_time_str(resultado.media_checkout_min)
        items = [f"<b>{vm.nome}</b> — {vm.valor}" for vm in resultado.abaixo_checkout]
        st.markdown(
            _card(f"Check-out antecipado (antes de {media_co_str})", items, "vermelho", "📥"),
            unsafe_allow_html=True,
        )

    if resultado.abaixo_tempo:
        algum = True
        items = [f"<b>{vm.nome}</b> — {int(vm.valor)} min" for vm in resultado.abaixo_tempo]
        st.markdown(
            _card(
                f"Tempo insuficiente no cliente (< {int(resultado.limiar_tempo)} min)",
                items, "vermelho", "⏳"
            ),
            unsafe_allow_html=True,
        )

    if resultado.nao_realizadas:
        algum = True
        items = [f"<b>{vm.nome}</b> — {vm.valor} visita(s)" for vm in resultado.nao_realizadas]
        st.markdown(
            _card("Visitas não realizadas", items, "vermelho", "❌"),
            unsafe_allow_html=True,
        )

    if resultado.somente_remota:
        algum = True
        items = [f"<b>{nome}</b>" for nome in resultado.somente_remota]
        st.markdown(
            _card("Apenas visitas remotas — ponto crítico de atenção", items, "amarelo", "⚠️"),
            unsafe_allow_html=True,
        )

    if not algum:
        st.success("Nenhum ponto negativo identificado neste período. 🎉")


def _render_ranking(resultado) -> None:
    """Renderiza os gráficos de ranking usando Streamlit nativo."""
    if resultado.ranking_aderencia:
        st.markdown('<p class="section-header">📊 Ranking de Aderência à Rota</p>', unsafe_allow_html=True)
        df_rank = pd.DataFrame(
            [(v.nome, v.aderencia) for v in resultado.ranking_aderencia],
            columns=["Vendedor", "Aderência (%)"],
        ).set_index("Vendedor")
        st.bar_chart(df_rank, color="#6366f1", use_container_width=True)

    if resultado.ranking_nao_realizadas:
        st.markdown('<p class="section-header">❌ Ranking de Visitas Não Realizadas</p>', unsafe_allow_html=True)
        # Filtra somente quem tem faltas para o gráfico ficar mais legível
        df_nr = pd.DataFrame(
            [(v.nome, int(v.valor)) for v in resultado.ranking_nao_realizadas if int(v.valor) > 0],
            columns=["Vendedor", "Não Realizadas"],
        )
        if not df_nr.empty:
            df_nr = df_nr.set_index("Vendedor")
            st.bar_chart(df_nr, color="#ef4444", use_container_width=True)
        else:
            st.success("Nenhuma visita não realizada! 🎯")

    if resultado.comparativo_pres_rem:
        st.markdown('<p class="section-header">🏢 Comparativo Presencial vs. Remoto por Vendedor</p>', unsafe_allow_html=True)
        df_comp = pd.DataFrame(
            [
                {
                    "Vendedor": v.nome,
                    "Presencial": v.visitas_pres,
                    "Remoto": v.visitas_rem,
                    "Não Realizada": v.visitas_nao,
                }
                for v in resultado.comparativo_pres_rem
            ]
        ).set_index("Vendedor")
        st.bar_chart(df_comp, color=["#22c55e", "#3b82f6", "#ef4444"], use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    col_title, col_btn = st.columns([0.85, 0.15])

    with col_title:
        st.title("📊 Rote Assist")

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("❌ Fechar"):
            os._exit(0)

    st.markdown("Faça o upload da sua planilha para gerar resumos e análises automáticas.")

    # 1. Upload de Arquivo (fora das abas — compartilhado)
    uploaded_file = st.file_uploader("Arraste e solte sua planilha (.xlsx, .csv)", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            df = loader.load(uploaded_file)
            st.success("✔ Arquivo carregado com sucesso!")

            with st.expander("📋 Dados Carregados (Pré-visualização)"):
                st.dataframe(df, use_container_width=True)

            # 2. Filtros compartilhados
            col1, col2 = st.columns(2)

            with col1:
                gestores_disponiveis = sorted(df["gestor"].dropna().unique().tolist())
                opcoes_gestor = ["Todos"] + gestores_disponiveis
                gestor_selecionado = st.selectbox("Selecione o Gestor:", opcoes_gestor)

            with col2:
                datas = st.date_input(
                    "Período do relatório (Início e Fim):",
                    value=(),
                    format="DD/MM/YYYY"
                )

                periodo = ""
                if isinstance(datas, (tuple, list)):
                    if len(datas) == 2:
                        inicio, fim = datas
                        if inicio.month == fim.month and inicio.year == fim.year:
                            periodo = f"{inicio.day:02d} a {fim.day:02d}/{fim.month:02d}"
                        else:
                            periodo = f"{inicio.day:02d}/{inicio.month:02d} a {fim.day:02d}/{fim.month:02d}"
                    elif len(datas) == 1:
                        periodo = f"{datas[0].day:02d}/{datas[0].month:02d}"

            gestor_filtro = None if gestor_selecionado == "Todos" else gestor_selecionado

            # ----------------------------------------------------------------
            # 3. ABAS
            # ----------------------------------------------------------------
            tab1, tab2 = st.tabs(["📤 Resumo", "🔍 Análise"])

            # ================================================================
            # ABA 1 — Resumo para Compartilhamento (comportamento original)
            # ================================================================
            with tab1:
                if st.button("Gerar Resumo", type="primary", key="btn_resumo"):
                    if not periodo:
                        st.warning("Por favor, preencha o período do relatório.")
                    else:
                        with st.spinner("Analisando dados..."):
                            try:
                                resultado = analyzer.analisar(df, periodo, gestor=gestor_filtro)
                                resumo = formatter.gerar_resumo(resultado)

                                st.subheader("✅ Resumo Gerado")
                                st.code(resumo, language="markdown")

                                st.markdown("---")
                                st.markdown("### Exportar Resumo")

                                col_btn1, col_btn2 = st.columns(2)

                                with col_btn1:
                                    st.download_button(
                                        label="📄 Baixar como .txt",
                                        data=resumo,
                                        file_name="resumo_visitas.txt",
                                        mime="text/plain",
                                    )

                                with col_btn2:
                                    with st.spinner("Gerando Imagem Premium..."):
                                        try:
                                            img_bytes = image_generator.gerar_imagem_html(resultado)
                                        except Exception:
                                            st.warning("Não foi possível gerar a imagem premium neste ambiente. Você pode baixar o resumo como .txt.")
                                            img_bytes = None
                                    if img_bytes:
                                        st.download_button(
                                            label="🖼️ Baixar como Imagem (.png)",
                                            data=img_bytes,
                                            file_name="resumo_visitas.png",
                                            mime="image/png",
                                        )

                            except ValueError as e:
                                st.error(f"Erro na análise: {e}")

            # ================================================================
            # ABA 2 — Análise Criteriosa
            # ================================================================
            with tab2:
                if st.button("🔍 Gerar Análise Criteriosa", type="primary", key="btn_analise"):
                    if not periodo:
                        st.warning("Por favor, preencha o período do relatório.")
                    else:
                        with st.spinner("Realizando análise criteriosa..."):
                            try:
                                resultado = analyzer.analisar(df, periodo, gestor=gestor_filtro)
                            except ValueError as e:
                                st.error(f"Erro na análise: {e}")
                                st.stop()

                        nome_gestor = resultado.gestor_selecionado or "Geral"
                        st.subheader(f"🔍 Análise Criteriosa — {nome_gestor}")
                        st.caption(f"Período: {resultado.periodo} · {resultado.total_vendedores} vendedor(es) analisado(s)")

                        # ---- Pontos Positivos ----
                        st.markdown('<p class="section-header">🟢 Pontos Positivos</p>', unsafe_allow_html=True)
                        _render_pontos_positivos(resultado)

                        # ---- Pontos Negativos ----
                        st.markdown("---")
                        st.markdown('<p class="section-header">🔴 Pontos de Atenção / Negativos</p>', unsafe_allow_html=True)
                        _render_pontos_negativos(resultado)

                        # ---- Gráficos de Ranking ----
                        st.markdown("---")
                        _render_ranking(resultado)

                        # ---- Insights para Decisão ----
                        st.markdown("---")
                        st.markdown('<p class="section-header">💡 Insights para Tomada de Decisão</p>', unsafe_allow_html=True)
                        lista_insights = insights_module.gerar_insights(resultado)
                        for ins in lista_insights:
                            st.markdown(_insight_card(ins), unsafe_allow_html=True)

                        # ---- Exportação ----
                        st.markdown("---")
                        st.markdown("### 📥 Exportar Análise")

                        col_exp1, col_exp2 = st.columns(2)

                        with col_exp1:
                            with st.spinner("Gerando imagem da análise..."):
                                try:
                                    img_analise = analysis_image_generator.gerar_imagem_analise(resultado)
                                except Exception:
                                    st.warning("Não foi possível gerar a imagem da análise neste ambiente. Tente baixar o PDF ou o resumo em texto.")
                                    img_analise = None
                            if img_analise:
                                st.download_button(
                                    label="🖼️ Baixar Análise como Imagem (.png)",
                                    data=img_analise,
                                    file_name="analise_criteriosa.png",
                                    mime="image/png",
                                    key="dl_analise_img",
                                )

                        with col_exp2:
                            # PDF via fpdf2 — gera PDF simples com o conteúdo da análise
                            with st.spinner("Gerando PDF..."):
                                pdf_bytes = _gerar_pdf_analise(resultado, lista_insights)
                            st.download_button(
                                label="📄 Baixar Análise como PDF",
                                data=pdf_bytes,
                                file_name="analise_criteriosa.pdf",
                                mime="application/pdf",
                                key="dl_analise_pdf",
                            )

        except Exception as e:
            st.error(f"Erro ao carregar a planilha: {e}")


# ---------------------------------------------------------------------------
# Gerador de PDF da Análise Criteriosa (fpdf2)
# ---------------------------------------------------------------------------

def _gerar_pdf_analise(resultado, lista_insights: list[dict]) -> bytes:
    """
    Gera um PDF da análise criteriosa usando fpdf2.
    Retorna os bytes do PDF.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        # Fallback: retorna um PDF mínimo com mensagem de erro
        return b"%PDF-1.4\n"

    from loader import minutes_to_time_str

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    # Ao gerar PDF com as fontes internas (p.ex. Helvetica), emojis podem causar erro
    # por não serem suportados pela fonte. Para uma correção rápida, removemos
    # caracteres emoji do texto antes de escrevê-lo no PDF.
    def _strip_emoji(text: str) -> str:
        if not isinstance(text, str):
            return text
        # Remove caracteres fora do Plano Multilingue Básico (BMP), que incluem
        # a maioria dos emojis (ord > 0xFFFF).
        return "".join(ch for ch in text if ord(ch) <= 0xFFFF)

    pdf.set_font("Helvetica", "B", 18)

    nome_gestor = resultado.gestor_selecionado or "Geral"

    # Título
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, f"Analise Criteriosa - {nome_gestor}", new_x="LMARGIN", new_y="NEXT", fill=True, align="C")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, f"Periodo: {resultado.periodo}  |  {resultado.total_vendedores} vendedor(es)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    def secao(titulo: str):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(0, 8, titulo, new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(2)

    def item(texto: str, cor=(51, 65, 85)):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*cor)
        pdf.cell(6)  # indent
        # Remove tags HTML básicas para o PDF e remove emojis
        texto_limpo = _strip_emoji(texto.replace("<b>", "").replace("</b>", ""))
        pdf.multi_cell(0, 6, f"  {texto_limpo}", new_x="LMARGIN", new_y="NEXT")

    # ---- Pontos Positivos ----
    secao("PONTOS POSITIVOS")

    if resultado.acima_aderencia:
        item(f"Aderencia acima da media ({int(resultado.media_aderencia)}%):", cor=(22, 101, 52))
        for vm in resultado.acima_aderencia:
            item(f"  - {vm.nome}: {int(vm.valor)}%", cor=(22, 101, 52))

    if resultado.abaixo_checkin:
        media_ci = minutes_to_time_str(resultado.media_checkin_min)
        item(f"Check-in pontual (antes de {media_ci}):", cor=(22, 101, 52))
        for vm in resultado.abaixo_checkin:
            item(f"  - {vm.nome}: {vm.valor}", cor=(22, 101, 52))

    if resultado.acima_tempo:
        item(f"Bom tempo no cliente (>= {int(resultado.limiar_tempo)} min):", cor=(22, 101, 52))
        for vm in resultado.acima_tempo:
            item(f"  - {vm.nome}: {int(vm.valor)} min", cor=(22, 101, 52))

    if resultado.sem_faltas:
        item("Zero visitas nao realizadas:", cor=(22, 101, 52))
        for nome in resultado.sem_faltas:
            item(f"  - {nome}", cor=(22, 101, 52))

    if not (resultado.acima_aderencia or resultado.abaixo_checkin or resultado.acima_tempo or resultado.sem_faltas):
        item("Nenhum ponto positivo identificado.")

    pdf.ln(4)

    # ---- Pontos Negativos ----
    secao("PONTOS DE ATENCAO / NEGATIVOS")

    if resultado.abaixo_aderencia:
        item(f"Aderencia abaixo da media ({int(resultado.media_aderencia)}%):", cor=(153, 27, 27))
        for vm in resultado.abaixo_aderencia:
            item(f"  - {vm.nome}: {int(vm.valor)}%", cor=(153, 27, 27))

    if resultado.acima_checkin:
        media_ci = minutes_to_time_str(resultado.media_checkin_min)
        item(f"Check-in tardio (depois de {media_ci}):", cor=(153, 27, 27))
        for vm in resultado.acima_checkin:
            item(f"  - {vm.nome}: {vm.valor}", cor=(153, 27, 27))

    if resultado.abaixo_checkout:
        media_co = minutes_to_time_str(resultado.media_checkout_min)
        item(f"Check-out antecipado (antes de {media_co}):", cor=(153, 27, 27))
        for vm in resultado.abaixo_checkout:
            item(f"  - {vm.nome}: {vm.valor}", cor=(153, 27, 27))

    if resultado.abaixo_tempo:
        item(f"Tempo insuficiente no cliente (< {int(resultado.limiar_tempo)} min):", cor=(153, 27, 27))
        for vm in resultado.abaixo_tempo:
            item(f"  - {vm.nome}: {int(vm.valor)} min", cor=(153, 27, 27))

    if resultado.nao_realizadas:
        item("Visitas nao realizadas:", cor=(153, 27, 27))
        for vm in resultado.nao_realizadas:
            item(f"  - {vm.nome}: {int(vm.valor)} visita(s)", cor=(153, 27, 27))

    if resultado.somente_remota:
        item("Apenas visitas remotas (ponto critico):", cor=(146, 64, 14))
        for nome in resultado.somente_remota:
            item(f"  - {nome}", cor=(146, 64, 14))

    pdf.ln(4)

    # ---- Ranking de Aderência ----
    secao("RANKING DE ADERENCIA A ROTA")
    for i, v in enumerate(resultado.ranking_aderencia, 1):
        item(f"{i}. {v.nome}: {int(v.aderencia)}%")

    pdf.ln(4)

    # ---- Insights ----
    secao("INSIGHTS PARA TOMADA DE DECISAO")
    tipo_cor = {
        "positivo": (22, 101, 52),
        "negativo": (153, 27, 27),
        "atencao":  (120, 53, 15),
        "neutro":   (51, 65, 85),
    }
    for ins in lista_insights:
        cor = tipo_cor.get(ins["tipo"], (51, 65, 85))
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*cor)
        pdf.multi_cell(0, 6, _strip_emoji(f"{ins['icone']} {ins['titulo']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(6)
        pdf.multi_cell(0, 5, _strip_emoji(f"   {ins['detalhe']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # Rodapé
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, "Visitas remotas nao sao consideradas no calculo da aderencia a rota.", align="C")

    return bytes(pdf.output())


if __name__ == "__main__":
    main()
