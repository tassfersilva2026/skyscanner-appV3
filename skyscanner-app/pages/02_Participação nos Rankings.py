# pages/02_Analise_Rankings.py
import streamlit as st
import pandas as pd
import numpy as np

from common import (
    apply_css, carregar_dados, CAMINHO_ARQUIVO, get_sidebar_filters,
    format_dates_in_df_for_display, render_footer, render_logo
)

st.set_page_config(page_title="Visão 2 — Participação nos Rankings",
                   layout="wide", initial_sidebar_state="expanded")
apply_css()
render_logo()

st.header("2. Análise de Participação nos Rankings")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado."); st.stop()

flt = get_sidebar_filters(df)
df_filtrado = flt['df_filtrado']
if df_filtrado.empty:
    st.info("Sem dados filtrados."); render_footer(df); st.stop()

# ===== Base: contagens por Ranking
counts = df_filtrado.groupby(['Agência/Companhia', 'RANKING']).size().unstack(fill_value=0)

# Ordena pela coluna de 1º lugar, se existir
if 1 in counts.columns or '1' in counts.columns:
    chave = 1 if 1 in counts.columns else '1'
    counts = counts.sort_values(by=chave, ascending=False)

# Totais linha/coluna
counts_tot = counts.copy()
counts_tot['Total'] = counts_tot.sum(axis=1)
counts_tot.loc['Total'] = counts_tot.sum(numeric_only=True, axis=0)

# ===== helper seguro para estilização (evita Too many indexers)
def style_safe(df_in: pd.DataFrame, fmt_str: str, cmap_name: str = 'Blues'):
    df_show = format_dates_in_df_for_display(df_in.copy())
    try:
        num_cols = df_show.select_dtypes(include='number').columns.tolist()
        sty = df_show.style.format(fmt_str)
        if num_cols:  # aplica gradiente só nas numéricas
            sty = sty.background_gradient(cmap=cmap_name, subset=num_cols)
        return sty
    except Exception:
        # se o Styler reclamar, volta sem estilo
        return df_show

# ==================== 2.1 Quantidade de Ofertas por Ranking (com Totais)
st.subheader("Quantidade de Ofertas por Ranking (com Totais)")
st.dataframe(style_safe(counts_tot, '{:,.0f}'))

# ==================== 2.2 Participação (%) por Ranking – dentro da Agência (linha)
st.subheader("Participação (%) por Ranking – dentro da Agência (linha)")
row_sums = counts.sum(axis=1).replace(0, np.nan)
pct_row = (counts.divide(row_sums, axis=0) * 100).fillna(0).round(2)

col_r1 = 1 if 1 in pct_row.columns else ('1' if '1' in pct_row.columns else None)
if col_r1 is not None:
    pct_row = pct_row.sort_values(by=col_r1, ascending=False)

st.dataframe(style_safe(pct_row, '{:.2f}%'))

# ==================== 2.3 Participação (%) por Ranking – dentro do Ranking (coluna)
st.subheader("Participação (%) por Ranking – dentro do Ranking (coluna)")
col_sums = counts.sum(axis=0).replace(0, np.nan)
pct_col = (counts.divide(col_sums, axis=1) * 100).fillna(0).round(2)

st.dataframe(style_safe(pct_col, '{:.2f}%'))

render_footer(df)
