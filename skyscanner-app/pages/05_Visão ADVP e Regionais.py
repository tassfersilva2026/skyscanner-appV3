# pages/05_Cascatas_123_MAX.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from common import (
    apply_css, carregar_dados, CAMINHO_ARQUIVO, get_sidebar_filters,
    REGIOES_TRECHOS_STD, ADVPS_ORDEM, chart_height_cascade,
    theme_plotly, COLOR_INCREASING, COLOR_DECREASING, render_footer, render_logo
)

st.set_page_config(page_title="Visão 5 — Cascatas (123 x MAX)", layout="wide", initial_sidebar_state="expanded")
apply_css()
render_logo()
st.header("5. Cascatas — 123MILHAS & MAXMILHAS")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado."); st.stop()

flt = get_sidebar_filters(df)
df_regiao = flt['df_regiao']
agencias_para_analise = flt['agencias_para_analise']
tipo_agencia_filtro = flt['tipo_agencia_filtro']
datas_sel = flt['datas_sel']
trecho_sel = flt['trecho_sel']
advp_valor = flt['advp_valor']
advp_range = flt['advp_range']

cias = ['GOL','LATAM','AZUL','JETSMART','TAP']

df_base = df_regiao.copy()
if tipo_agencia_filtro == 'Agências':
    df_base = df_base[~df_base['Agência/Companhia'].isin(cias)]
elif tipo_agencia_filtro == 'Cias':
    df_base = df_base[df_base['Agência/Companhia'].isin(cias + ['123MILHAS','MAXMILHAS'])]

if advp_valor != 'Todos':
    df_base = df_base[df_base['ADVP'] == advp_valor]
else:
    df_base = df_base[(df_base['ADVP'] >= advp_range[0]) & (df_base['ADVP'] <= advp_range[1])]

if len(datas_sel) == 2:
    sd, ed = pd.to_datetime(datas_sel[0]), pd.to_datetime(datas_sel[1])
    df_base = df_base[(df_base['Data/Hora da Busca'].dt.date >= sd.date()) &
                      (df_base['Data/Hora da Busca'].dt.date <= ed.date())]

if trecho_sel != 'Todos os Trechos':
    df_base = df_base[df_base['TRECHO'] == trecho_sel]

alvo = set(agencias_para_analise) | {'123MILHAS','MAXMILHAS'}
df_base = df_base[df_base['Agência/Companhia'].isin([x for x in df_base['Agência/Companhia'].unique() if x in alvo])]

if df_base.empty:
    st.info("Sem dados para as cascatas com os filtros atuais."); render_footer(df); st.stop()

def diffs_por_advp(dfin: pd.DataFrame, agencia_ref: str) -> pd.DataFrame:
    rows=[]
    if dfin.empty or agencia_ref not in dfin['Agência/Companhia'].unique(): 
        return pd.DataFrame(rows)
    advps_pres = sorted({int(x) for x in dfin['ADVP'].dropna().unique()})
    advps = [a for a in ADVPS_ORDEM if a in advps_pres]
    for advp in advps:
        d = dfin[dfin['ADVP'] == advp]
        preco_ag = d.loc[d['Agência/Companhia'] == agencia_ref, 'Preço'].mean()
        comp = d[~d['Agência/Companhia'].isin(['123MILHAS','MAXMILHAS'])]
        if pd.isna(preco_ag) or comp.empty: 
            continue
        best = comp.groupby('Agência/Companhia')['Preço'].mean().min()
        if pd.isna(best) or best == 0:
            continue
        diff = (preco_ag - best) / best * 100
        rows.append({'ADVP': str(advp), 'DifPct': diff, 'LabelPct': f"{diff:.2f}%"})
    return pd.DataFrame(rows)

def diffs_por_regiao(dfin: pd.DataFrame, agencia_ref: str) -> pd.DataFrame:
    rows=[]
    if dfin.empty or agencia_ref not in dfin['Agência/Companhia'].unique():
        return pd.DataFrame(rows)
    for reg, std_set in REGIOES_TRECHOS_STD.items():
        dreg = dfin[dfin['TRECHO_STD'].isin(std_set)]
        if dreg.empty: 
            continue
        preco_ag = dreg.loc[dreg['Agência/Companhia'] == agencia_ref, 'Preço'].mean()
        comp = dreg[~dreg['Agência/Companhia'].isin(['123MILHAS','MAXMILHAS'])]
        if pd.isna(preco_ag) or comp.empty:
            continue
        best = comp.groupby('Agência/Companhia')['Preço'].mean().min()
        if pd.isna(best) or best == 0:
            continue
        diff = (preco_ag - best) / best * 100
        rows.append({'REGIÃO': reg, 'DifPct': diff, 'LabelPct': f"{diff:.2f}%"})
    return pd.DataFrame(rows)

def waterfall_simple(dfplot: pd.DataFrame, xcol: str, title: str):
    if dfplot.empty:
        return None
    fig = go.Figure(go.Waterfall(
        x=list(dfplot[xcol]),
        measure=['relative'] * len(dfplot),
        y=list(dfplot['DifPct']),
        text=list(dfplot['LabelPct']),
        textposition='outside',
        connector={'line': {'color': 'rgba(0,0,0,0.25)'}},
        increasing={'marker': {'color': COLOR_INCREASING}},
        decreasing={'marker': {'color': COLOR_DECREASING}},
    ))
    fig.update_traces(texttemplate='<b>%{text}</b>', textfont_size=26, cliponaxis=False)
    fig.update_layout(
        title=title, height=chart_height_cascade,
        xaxis=dict(type='category'),
        yaxis=dict(title='Diferença vs Melhor Concorrente (%)', tickformat=".2f", ticksuffix='%'),
        margin=dict(t=70, b=60)
    )
    return theme_plotly(fig)

st.subheader("5.1 123MILHAS & MAXMILHAS por ADVP (Cascata)")
for ag in ['123MILHAS','MAXMILHAS']:
    if ag not in df_base['Agência/Companhia'].unique():
        st.info(f"Sem dados de **{ag}** nos filtros atuais.")
        continue
    data_ag = diffs_por_advp(df_base, ag)
    if data_ag.empty:
        st.info(f"Sem comparativo por ADVP para **{ag}**.")
        continue
    data_ag['ADVP'] = pd.Categorical(data_ag['ADVP'], categories=[str(x) for x in ADVPS_ORDEM], ordered=True)
    data_ag = data_ag.sort_values('ADVP')
    fig = waterfall_simple(data_ag, 'ADVP', f"{ag} por ADVP (Cascata)")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("5.2 Diferença vs Melhor Concorrente por Região (Cascata)")
for ag in ['123MILHAS','MAXMILHAS']:
    if ag not in df_base['Agência/Companhia'].unique():
        st.info(f"Sem dados regionais de **{ag}** nos filtros atuais.")
        continue
    data_reg = diffs_por_regiao(df_base, ag)
    if data_reg.empty:
        st.info(f"Sem comparativo por Região para **{ag}**.")
        continue
    data_reg = data_reg.sort_values('REGIÃO')
    fig = waterfall_simple(data_reg, 'REGIÃO', f"{ag} por Região (Cascata)")
    st.plotly_chart(fig, use_container_width=True)

render_footer(df)
