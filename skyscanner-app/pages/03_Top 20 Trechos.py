# pages/03_Vantagem_Trecho.py
import streamlit as st
import pandas as pd
from collections import Counter as C

from common import (
    apply_css, carregar_dados, CAMINHO_ARQUIVO, get_sidebar_filters,
    apply_filters_for_timeseries, format_dates_in_df_for_display, render_footer, render_logo
)

st.set_page_config(page_title="Visão 3 — Vantagem por Trecho", layout="wide", initial_sidebar_state="expanded")
apply_css()
render_logo()
st.header("3. Análise de Vantagem Competitiva por Trecho")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado."); st.stop()

flt = get_sidebar_filters(df)

# Mantém 123 e MAX separados
df_base = apply_filters_for_timeseries(
    df_regiao=flt['df_regiao'],
    tipo_agencia_filtro=flt['tipo_agencia_filtro'],
    advp_valor=flt['advp_valor'],
    advp_range=flt['advp_range'],
    datas_sel=flt['datas_sel'],
    trecho_sel=flt['trecho_sel'],
    agencias_para_analise=flt['agencias_para_analise'],
)

if df_base.empty:
    st.info("Sem dados para a análise com os filtros atuais."); render_footer(df); st.stop()

base = df_base[['TRECHO','Data/Hora da Busca','Agência/Companhia','Preço','RANKING']].dropna()
base = base[base['RANKING'].isin([1,2,3])].copy()
if base.empty:
    st.info("Sem posições 1–3 para comparar."); render_footer(df); st.stop()

pv = (base.pivot_table(index=['TRECHO','Data/Hora da Busca'],
                       columns='RANKING',
                       values=['Preço','Agência/Companhia'],
                       aggfunc='first').reset_index())
pv.columns = ['_'.join(map(str,c)).strip('_') for c in pv.columns.to_flat_index()]
pv = pv.rename(columns={
    'TRECHO':'TRECHO',
    'Data/Hora da Busca':'Data/Hora da Busca',
    'Preço_1':'Preço_1', 'Preço_2':'Preço_2', 'Preço_3':'Preço_3',
    'Agência/Companhia_1':'Agência_1', 'Agência/Companhia_2':'Agência_2', 'Agência/Companhia_3':'Agência_3'
})

pv = pv.dropna(subset=['Preço_1','Preço_2','Agência_1','Agência_2'])
pv = pv[pv['Agência_1'] != pv['Agência_2']]
if pv.empty:
    st.info("Não há comparativos válidos de 1º vs 2º com os filtros."); render_footer(df); st.stop()

pv['Diferença_2_pct'] = ((pv['Preço_2'] - pv['Preço_1']) / pv['Preço_1'] * 100).round(2)
pv['Diferença_3_pct'] = ((pv['Preço_3'] - pv['Preço_1']) / pv['Preço_1'] * 100).round(2) if 'Preço_3' in pv.columns else pd.NA

def tabela_top(ag: str):
    d = pv[pv['Agência_1'] == ag]
    if d.empty:
        st.info(f"Sem vitórias para **{ag}** nos filtros atuais.")
        return

    top = (d.groupby('TRECHO')
             .agg(
                 Vitorias=('TRECHO','count'),
                 Menor_Preco_1=('Preço_1','min'),
                 Menor_Preco_2=('Preço_2','min'),
                 Diferenca_Media_2=('Diferença_2_pct','mean'),
                 Menor_Preco_3=('Preço_3','min'),
                 Diferenca_Media_3=('Diferença_3_pct','mean')
             )
             .sort_values('Diferenca_Media_2', ascending=False)
             .head(20)
             .reset_index())

    seg = d.groupby('TRECHO')['Agência_2'].agg(lambda x: C(x).most_common(1)[0][0]).reset_index()
    ter = d.groupby('TRECHO')['Agência_3'].agg(lambda x: C(x.dropna()).most_common(1)[0][0] if x.notna().any() else None).reset_index()

    top = top.merge(seg, on='TRECHO', how='left').merge(ter, on='TRECHO', how='left')
    top = top[[
        'TRECHO','Vitorias','Menor_Preco_1','Agência_2','Menor_Preco_2','Diferenca_Media_2',
        'Agência_3','Menor_Preco_3','Diferenca_Media_3'
    ]].rename(columns={
        'Menor_Preco_1':'Menor Preço 1º Lugar',
        'Agência_2':'2º Lugar',
        'Menor_Preco_2':'Menor Preço 2º Lugar',
        'Diferenca_Media_2':'Diferença (%) para 2º',
        'Agência_3':'3º Lugar',
        'Menor_Preco_3':'Menor Preço 3º Lugar',
        'Diferenca_Media_3':'Diferença (%) para 3º'
    })

    st.subheader(f"Top 20 Trechos — {ag} (Vitórias)")
    st.dataframe(
        format_dates_in_df_for_display(top).style.background_gradient(cmap='Blues').format({
            'Menor Preço 1º Lugar':'R$ {:,.2f}',
            'Menor Preço 2º Lugar':'R$ {:,.2f}',
            'Menor Preço 3º Lugar':'R$ {:,.2f}',
            'Diferença (%) para 2º':'{:.2f}%',
            'Diferença (%) para 3º':'{:.2f}%'
        })
    )

tabela_top('123MILHAS')
tabela_top('MAXMILHAS')

render_footer(df)
