# pages/01_Visao_Geral.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from common import (
    apply_css, carregar_dados, CAMINHO_ARQUIVO, get_sidebar_filters,
    build_color_map, theme_plotly, chart_height, largura_barras_precos,
    COLOR_123, COLOR_MAX, PRIMARY_BLUE, render_footer, render_logo
)

st.set_page_config(page_title="Visão 1 — Preços por Agência", layout="wide", initial_sidebar_state="expanded")
apply_css()
render_logo()

st.header("1. Comparação de Preços por Agência")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado."); st.stop()

flt = get_sidebar_filters(df)
df_filtrado = flt['df_filtrado']
agencias_principais = flt['agencias_principais']
config_123_max_filtro = flt['config_123_max_filtro']

if df_filtrado.empty:
    st.info("Sem dados filtrados."); render_footer(df); st.stop()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Agências Principais")
    alvo = (['Grupo123'] if config_123_max_filtro == 'Grupo123' else agencias_principais)
    df_princ = df_filtrado[df_filtrado['Agência/Companhia'].isin(alvo)]

    if not df_princ.empty:
        pm = df_princ.groupby('Agência/Companhia', as_index=False)['Preço'].mean()
        cmap = build_color_map(pm['Agência/Companhia'].unique())
        fig = px.bar(
            pm, x='Agência/Companhia', y='Preço', text='Preço',
            title='Preço Médio', labels={'Agência/Companhia': 'Agência', 'Preço': 'Preço Médio (R$)'},
            color='Agência/Companhia', color_discrete_map=cmap
        )
        fig.update_layout(yaxis_title='Preço Médio (R$)', height=chart_height)
        fig.update_traces(
            texttemplate='<b>R$ %{y:,.0f}</b>', textposition='inside',
            insidetextfont=dict(size=18, color='white'), width=largura_barras_precos
        )
        theme_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados das principais.")

with c2:
    st.subheader("Agências Concorrentes")
    if config_123_max_filtro == 'Grupo123':
        df_conc = df_filtrado[df_filtrado['Agência/Companhia'] != 'Grupo123']
    else:
        df_conc = df_filtrado[~df_filtrado['Agência/Companhia'].isin(agencias_principais)]

    if not df_conc.empty:
        pm = df_conc.groupby('Agência/Companhia', as_index=False)['Preço'].mean().sort_values('Preço')
        cmap = build_color_map(pm['Agência/Companhia'].unique(), include_named=False)
        fig = px.bar(
            pm, x='Agência/Companhia', y='Preço', text='Preço',
            title='Preço Médio', labels={'Agência/Companhia': 'Agência', 'Preço': 'Preço Médio (R$)'},
            color='Agência/Companhia', color_discrete_map=cmap
        )
        fig.update_layout(yaxis_title='Preço Médio (R$)', height=chart_height)
        fig.update_traces(
            texttemplate='<b>R$ %{y:,.0f}</b>', textposition='inside',
            insidetextfont=dict(size=18, color='white'), width=largura_barras_precos
        )
        theme_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de concorrentes.")

st.header("2. Comparativo de Preços vs. Melhor Concorrente")

if config_123_max_filtro == 'Grupo123':
    df_comp = df_filtrado[df_filtrado['Agência/Companhia'] != 'Grupo123']
    pm_grupo = df_filtrado.loc[df_filtrado['Agência/Companhia'] == 'Grupo123', 'Preço'].mean()
    if not df_comp.empty:
        melhor = df_comp.groupby('Agência/Companhia')['Preço'].mean().min()
        if pd.notna(melhor):
            diff = ((pm_grupo - melhor) / melhor) * 100 if pd.notna(pm_grupo) else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=diff,
                title={'text': "Grupo123 vs. Melhor Concorrente (%)"},
                number={'suffix': '%', 'valueformat': '.0f'},
                gauge={'axis': {'range': [-50, 50]}, 'bar': {'color': PRIMARY_BLUE}, 'bgcolor': 'white'}
            ))
            fig.update_layout(height=chart_height)
            theme_plotly(fig)
            st.plotly_chart(fig, use_container_width=True)
else:
    df_comp = df_filtrado[~df_filtrado['Agência/Companhia'].isin(['123MILHAS', 'MAXMILHAS'])]
    if not df_comp.empty:
        melhor = df_comp.groupby('Agência/Companhia')['Preço'].mean().min()
        pm_123 = df_filtrado.loc[df_filtrado['Agência/Companhia'] == '123MILHAS', 'Preço'].mean()
        pm_max = df_filtrado.loc[df_filtrado['Agência/Companhia'] == 'MAXMILHAS', 'Preço'].mean()
        if pd.notna(melhor):
            d123 = ((pm_123 - melhor) / melhor) * 100 if pd.notna(pm_123) else 0
            dmax = ((pm_max - melhor) / melhor) * 100 if pd.notna(pm_max) else 0
            g1, g2 = st.columns(2)
            with g1:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=d123,
                    title={'text': "123MILHAS vs. Melhor Concorrente (%)"},
                    number={'suffix': '%', 'valueformat': '.0f'},
                    gauge={'axis': {'range': [-50, 50]}, 'bar': {'color': COLOR_123}, 'bgcolor': 'white'}
                ))
                fig.update_layout(height=chart_height)
                theme_plotly(fig)
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=dmax,
                    title={'text': "MAXMILHAS vs. Melhor Concorrente (%)"},
                    number={'suffix': '%', 'valueformat': '.0f'},
                    gauge={'axis': {'range': [-50, 50]}, 'bar': {'color': COLOR_MAX}, 'bgcolor': 'white'}
                ))
                fig.update_layout(height=chart_height)
                theme_plotly(fig)
                st.plotly_chart(fig, use_container_width=True)

render_footer(df)
