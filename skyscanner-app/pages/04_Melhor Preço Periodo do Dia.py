# pages/04_Melhor_Preco_Por_Periodo.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from common import (
    apply_css, carregar_dados, CAMINHO_ARQUIVO, get_sidebar_filters,
    build_color_map, theme_plotly, chart_height, render_footer, render_logo
)

st.set_page_config(page_title="Visão 4 — Melhor Preço por Período do Dia", layout="wide", initial_sidebar_state="expanded")
apply_css()
render_logo()

st.header("4. Ranking de Melhor Preço por Período do Dia")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado."); st.stop()

flt = get_sidebar_filters(df)
df_filtrado = flt['df_filtrado']
agencias_principais = flt['agencias_principais']
config_123_max_filtro = flt['config_123_max_filtro']

hora_col = None
for cand in ['Horário1','Horário2','Horário3']:
    if cand in df_filtrado.columns:
        hora_col = cand
        break

if not hora_col:
    st.warning("Não há coluna de horário (Horário1/2/3) para esta análise.")
    render_footer(df); st.stop()

df_h = df_filtrado.copy()
df_h[hora_col] = pd.to_datetime(df_h[hora_col], errors='coerce')
df_h = df_h.dropna(subset=[hora_col])
if df_h.empty:
    st.info("Sem horários válidos após aplicar os filtros.")
    render_footer(df); st.stop()

df_h['Hora do Voo'] = df_h[hora_col].dt.hour

series_list = []

best_by_hour = df_h.groupby('Hora do Voo')['Preço'].min().reset_index()
best_by_hour['Agência'] = 'Melhor Preço'
best_by_hour.rename(columns={'Preço':'Preço (R$)'}, inplace=True)
series_list.append(best_by_hour)

if config_123_max_filtro == 'Grupo123':
    if 'Grupo123' in df_h['Agência/Companhia'].unique():
        g = (df_h[df_h['Agência/Companhia'] == 'Grupo123']
             .groupby('Hora do Voo')['Preço'].min().reset_index())
        g['Agência'] = 'Grupo123'
        g.rename(columns={'Preço':'Preço (R$)'}, inplace=True)
        series_list.append(g)
else:
    for ag in ['123MILHAS','MAXMILHAS']:
        if ag in df_h['Agência/Companhia'].unique():
            s = (df_h[df_h['Agência/Companhia'] == ag]
                 .groupby('Hora do Voo')['Preço'].min().reset_index())
            s['Agência'] = ag
            s.rename(columns={'Preço':'Preço (R$)'}, inplace=True)
            series_list.append(s)

if len(series_list) == 1 and agencias_principais:
    for ag in agencias_principais:
        if ag in df_h['Agência/Companhia'].unique():
            s = (df_h[df_h['Agência/Companhia'] == ag]
                 .groupby('Hora do Voo')['Preço'].min().reset_index())
            s['Agência'] = ag
            s.rename(columns={'Preço':'Preço (R$)'}, inplace=True)
            series_list.append(s)

df_plot = pd.concat(series_list, ignore_index=True) if series_list else pd.DataFrame(columns=['Hora do Voo','Preço (R$)','Agência'])
if df_plot.empty:
    st.info("Sem séries para plotar com os filtros atuais.")
    render_footer(df); st.stop()

cmap = build_color_map(df_plot['Agência'].unique())

periodos = [
    ("Madrugada", range(0,6)),
    ("Manhã",     range(6,12)),
    ("Tarde",     range(12,18)),
    ("Noite",     range(18,24)),
]

for nome, horas in periodos:
    d = df_plot[df_plot['Hora do Voo'].isin(horas)].copy()
    if d.empty:
        continue
    fig = px.line(
        d, x='Hora do Voo', y='Preço (R$)', color='Agência', markers=True,
        title=nome, color_discrete_map=cmap
    )
    fig.update_traces(hovertemplate="%{fullData.name}<br>Hora: %{x}<br>Preço: R$ %{y:.2f}")
    fig.update_layout(height=chart_height, xaxis=dict(dtick=1), yaxis_title='Preço (R$)')
    theme_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)

render_footer(df)
