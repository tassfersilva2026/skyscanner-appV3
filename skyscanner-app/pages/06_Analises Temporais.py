# pages/06_Visoes_Temporais.py
import streamlit as st
import pandas as pd
import numpy as np

from common import (
    apply_css, carregar_dados, CAMINHO_ARQUIVO, get_sidebar_filters,
    apply_filters_for_timeseries, add_period_column,
    build_blue_gray_map, line_fig, REGIOES_TRECHOS_STD, ADVPS_ORDEM,
    render_footer, render_logo
)

st.set_page_config(page_title="Visão 6 — Visões Temporais", layout="wide", initial_sidebar_state="expanded")
apply_css()
render_logo()
st.header("6. Visões Temporais — Semanal / Quinzenal / Mensal")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado."); st.stop()

flt = get_sidebar_filters(df)
df_regiao = flt['df_regiao']
tipo_agencia_filtro = flt['tipo_agencia_filtro']
advp_valor = flt['advp_valor']
advp_range = flt['advp_range']
datas_sel = flt['datas_sel']
trecho_sel = flt['trecho_sel']
agencias_para_analise = flt['agencias_para_analise']

st.markdown('<div class="topbar"><span class="label">Agregação temporal:</span></div>', unsafe_allow_html=True)
visao = st.radio(" ", options=['Semanal','Quinzenal','Mensal'], index=0, horizontal=True, label_visibility="collapsed")
st.markdown("")

df_ts_base = apply_filters_for_timeseries(df_regiao, tipo_agencia_filtro, advp_valor, advp_range,
                                          datas_sel, trecho_sel, agencias_para_analise)
if df_ts_base.empty:
    st.info("Sem dados para séries temporais com os filtros atuais."); render_footer(df); st.stop()

sd_ts = pd.to_datetime(datas_sel[0]); ed_ts = pd.to_datetime(datas_sel[1])
df_ts = add_period_column(df_ts_base, visao, sd_ts, ed_ts)

def top3_competitors(df_in: pd.DataFrame, exclude=('123MILHAS','MAXMILHAS')) -> list:
    comp = df_in[~df_in['Agência/Companhia'].isin(exclude)]
    if comp.empty: return []
    return list(comp.groupby('Agência/Companhia').size().sort_values(ascending=False).head(3).index)

top3 = top3_competitors(df_ts)
alvo_agencias = [a for a in ['123MILHAS','MAXMILHAS'] if a in df_ts['Agência/Companhia'].unique()] + top3

st.subheader("6.1 Agências Principais VS Concorrentes — Preço Médio por Período")
g = (df_ts[df_ts['Agência/Companhia'].isin(alvo_agencias)]
     .groupby(['PERIODO','Agência/Companhia'])['Preço'].mean().reset_index())
if not g.empty:
    cmap = build_blue_gray_map(g['Agência/Companhia'].unique())
    fig = line_fig(g, 'PERIODO', 'Preço', 'Agência/Companhia',
                   f"Média de Preço ({visao}) – 123, MAX e TOP-3", percent=False, cmap=cmap)
    fig.update_yaxes(title_text="Preço (R$)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem dados para preço médio.")

st.subheader("6.2 Quantidade de Ofertas por Ranking (com Totais) — 123, MAX e TOP-3")
gtot = (df_ts[df_ts['Agência/Companhia'].isin(alvo_agencias)]
        .groupby(['PERIODO','Agência/Companhia']).size().reset_index(name='Ofertas'))
if not gtot.empty:
    cmap = build_blue_gray_map(gtot['Agência/Companhia'].unique())
    figt = line_fig(gtot, 'PERIODO', 'Ofertas', 'Agência/Companhia',
                    f"Total de Ofertas ({visao})", percent=False, cmap=cmap)
    figt.update_yaxes(title_text="Qtd Ofertas")
    st.plotly_chart(figt, use_container_width=True)
else:
    st.info("Sem dados de ofertas totais.")

tabs = st.tabs(["Ranking 1", "Ranking 2", "Ranking 3"])
for rnk, t in zip([1,2,3], tabs):
    with t:
        gr = (df_ts[(df_ts['RANKING']==rnk) & (df_ts['Agência/Companhia'].isin(alvo_agencias))]
              .groupby(['PERIODO','Agência/Companhia']).size().reset_index(name='Ofertas'))
        if gr.empty: st.info("Sem dados"); continue
        cmap = build_blue_gray_map(gr['Agência/Companhia'].unique())
        fgr = line_fig(gr, 'PERIODO', 'Ofertas', 'Agência/Companhia',
                       f"Ofertas de Ranking {rnk} ({visao})", percent=False, cmap=cmap)
        fgr.update_yaxes(title_text="Qtd Ofertas")
        st.plotly_chart(fgr, use_container_width=True)

st.subheader("6.3 Participação (%) por Ranking – dentro do Ranking (coluna)")
tabs2 = st.tabs(["Ranking 1", "Ranking 2", "Ranking 3"])
for rnk, t in zip([1,2,3], tabs2):
    with t:
        base_r = df_ts[df_ts['RANKING']==rnk]
        if base_r.empty: st.info("Sem dados"); continue
        cnt = base_r.groupby(['PERIODO','Agência/Companhia']).size().reset_index(name='Q')
        tot = cnt.groupby('PERIODO')['Q'].sum().reset_index(name='TOT')
        share = cnt.merge(tot, on='PERIODO')
        share['Participação (%)'] = (share['Q']/share['TOT']*100).round(2)
        share = share[share['Agência/Companhia'].isin(alvo_agencias)]
        if share.empty: st.info("Sem dados"); continue
        cmap = build_blue_gray_map(share['Agência/Companhia'].unique())
        fsh = line_fig(share, 'PERIODO', 'Participação (%)', 'Agência/Companhia',
                       f"Share no Ranking {rnk} ({visao})", percent=True, cmap=cmap)
        st.plotly_chart(fsh, use_container_width=True)

st.subheader("6.4 Ranking de Melhor Preço por Período do Dia (hora e data)")
dH = df_ts.copy()
dH['HORA'] = dH['Data/Hora da Busca'].dt.floor('H')
ag_series = []
for ag in [a for a in ['123MILHAS','MAXMILHAS'] if a in dH['Agência/Companhia'].unique()]:
    s = dH[dH['Agência/Companhia']==ag].groupby('HORA')['Preço'].min().reset_index()
    s['Série'] = ag; ag_series.append(s)
smin = dH.groupby('HORA')['Preço'].min().reset_index(); smin['Série'] = 'Melhor Preço'; ag_series.append(smin)
if ag_series:
    dfHplot = pd.concat(ag_series, ignore_index=True)
    cmapH = build_blue_gray_map(dfHplot['Série'].unique())
    figH = line_fig(dfHplot, 'HORA', 'Preço', 'Série',
                    "Preço mínimo por hora (123, MAX e Melhor Preço)", percent=False, cmap=cmapH)
    figH.update_yaxes(title_text="Preço (R$)")
    st.plotly_chart(figH, use_container_width=True)
else:
    st.info("Sem dados horários.")

st.subheader("6.5 Diferença vs Melhor Concorrente por ADVP — 123 e MAX (linhas)")
def diff_vs_best_by_period_advp(df_in, ag):
    rows=[]
    if df_in.empty or ag not in df_in['Agência/Companhia'].unique(): return pd.DataFrame()
    advps = sorted([int(x) for x in df_in['ADVP'].dropna().unique()])
    for advp in advps:
        d = df_in[df_in['ADVP']==advp]
        if d.empty: continue
        d = add_period_column(d, visao, sd_ts, ed_ts)
        grp = d.groupby('PERIODO')
        for per, dfp in grp:
            pm_ag = dfp.loc[dfp['Agência/Companhia']==ag,'Preço'].mean()
            comp = dfp[~dfp['Agência/Companhia'].isin(['123MILHAS','MAXMILHAS'])]
            if pd.isna(pm_ag) or comp.empty: continue
            best = comp.groupby('Agência/Companhia')['Preço'].mean().min()
            if pd.isna(best) or best==0: continue
            rows.append({'PERIODO':per,'ADVP':str(advp),'Diferença (%)':(pm_ag-best)/best*100})
    return pd.DataFrame(rows)

for ag in [a for a in ['123MILHAS','MAXMILHAS'] if a in df_ts['Agência/Companhia'].unique()]:
    dd = diff_vs_best_by_period_advp(df_ts, ag)
    if dd.empty: st.info(f"Sem dados por ADVP para {ag}."); continue
    figd = line_fig(dd, 'PERIODO', 'Diferença (%)', 'ADVP',
                    f"{ag} – Diferença vs Melhor Concorrente por ADVP ({visao})",
                    percent=True, cmap=build_blue_gray_map(dd['ADVP'].unique()))
    st.plotly_chart(figd, use_container_width=True)

st.subheader("6.6 Diferença vs Melhor Concorrente por Região — 123 e MAX (linhas)")
def diff_vs_best_by_period_region(df_in, ag):
    rows=[]
    if df_in.empty or ag not in df_in['Agência/Companhia'].unique(): return pd.DataFrame()
    d = add_period_column(df_in, visao, sd_ts, ed_ts)
    for reg,std_set in REGIOES_TRECHOS_STD.items():
        dr = d[d['TRECHO_STD'].isin(std_set)]
        if dr.empty: continue
        grp = dr.groupby('PERIODO')
        for per, dfp in grp:
            pm_ag = dfp.loc[dfp['Agência/Companhia']==ag,'Preço'].mean()
            comp = dfp[~dfp['Agência/Companhia'].isin(['123MILHAS','MAXMILHAS'])]
            if pd.isna(pm_ag) or comp.empty: continue
            best = comp.groupby('Agência/Companhia')['Preço'].mean().min()
            if pd.isna(best) or best==0: continue
            rows.append({'PERIODO':per,'REGIÃO':reg,'Diferença (%)':(pm_ag-best)/best*100})
    return pd.DataFrame(rows)

for ag in [a for a in ['123MILHAS','MAXMILHAS'] if a in df_ts['Agência/Companhia'].unique()]:
    dr = diff_vs_best_by_period_region(df_ts, ag)
    if dr.empty: st.info(f"Sem dados regionais para {ag}."); continue
    vol = (df_ts.groupby('TRECHO_STD').size().reset_index(name='n'))
    reg_rank = []
    for reg in REGIOES_TRECHOS_STD.keys():
        std = REGIOES_TRECHOS_STD[reg]
        reg_rank.append((reg, int(vol[vol['TRECHO_STD'].isin(std)]['n'].sum())))
    top_regs = [r for r,_ in sorted(reg_rank, key=lambda x:x[1], reverse=True)[:5] if _>0]
    dplot = dr[dr['REGIÃO'].isin(top_regs)] if top_regs else dr
    figdr = line_fig(dplot, 'PERIODO', 'Diferença (%)', 'REGIÃO',
                     f"{ag} – Diferença vs Melhor Concorrente por Região ({visao})",
                     percent=True, cmap=build_blue_gray_map(dplot['REGIÃO'].unique()))
    st.plotly_chart(figdr, use_container_width=True)

st.subheader("6.7 Comparativo de Preços vs. Melhor Concorrente — Agências Principais")
def diff_vs_best_by_period(df_in, ag):
    d = add_period_column(df_in, visao, sd_ts, ed_ts)
    rows=[]
    for per, dfp in d.groupby('PERIODO'):
        pm_ag = dfp.loc[dfp['Agência/Companhia']==ag,'Preço'].mean()
        comp = dfp[~dfp['Agência/Companhia'].isin(['123MILHAS','MAXMILHAS'])]
        if pd.isna(pm_ag) or comp.empty: continue
        best = comp.groupby('Agência/Companhia')['Preço'].mean().min()
        if pd.isna(best) or best==0: continue
        rows.append({'PERIODO':per,'Agência':ag,'Diferença (%)':(pm_ag-best)/best*100})
    return pd.DataFrame(rows)

lines=[]
for ag in [a for a in ['123MILHAS','MAXMILHAS'] if a in df_ts['Agência/Companhia'].unique()]:
    d = diff_vs_best_by_period(df_ts, ag)
    if not d.empty: lines.append(d)
if lines:
    dall = pd.concat(lines, ignore_index=True)
    cmapA = build_blue_gray_map(dall['Agência'].unique())
    figA = line_fig(dall, 'PERIODO', 'Diferença (%)', 'Agência',
                    f"Diferença vs Melhor Concorrente ({visao}) – 123 x MAX",
                    percent=True, cmap=cmapA)
    st.plotly_chart(figA, use_container_width=True)
else:
    st.info("Sem dados para comparativo por agência.")

st.subheader("6.8 Quantidade de Ofertas por Ranking (123, MAX e Melhor Preço) — por hora")
dhr = df_ts.copy(); dhr['HORA'] = dhr['Data/Hora da Busca'].dt.floor('H')
series=[]
for ag in [a for a in ['123MILHAS','MAXMILHAS'] if a in dhr['Agência/Companhia'].unique()]:
    s = dhr.groupby(['HORA','RANKING','Agência/Companhia']).size().reset_index(name='Ofertas')
    s = s[s['Agência/Companhia']==ag]; s['Série']=ag; series.append(s)
win = dhr[dhr['RANKING']==1].groupby(['HORA']).size().reset_index(name='Ofertas')
win['RANKING']=1; win['Agência/Companhia']='*'; win['Série']='Melhor Preço'; series.append(win)
if series:
    dfR = pd.concat(series, ignore_index=True)
    for rnk in [1,2,3]:
        dplot = dfR[dfR['RANKING']==rnk]
        if dplot.empty: continue
        cmapR = build_blue_gray_map(dplot['Série'].unique())
        fr = line_fig(dplot, 'HORA', 'Ofertas', 'Série',
                      f"Ranking {rnk} por hora", percent=False, cmap=cmapR)
        fr.update_yaxes(title_text="Qtd Ofertas")
        st.plotly_chart(fr, use_container_width=True)
else:
    st.info("Sem dados por hora.")

st.subheader("6.9 Participação (%) por Ranking – dentro da Agência (linha) — por hora")
dpa = dhr.copy()
out=[]
tot_mkt = dpa.groupby('HORA').size().reset_index(name='TOT')
win_mkt = dpa[dpa['RANKING']==1].groupby('HORA').size().reset_index(name='WIN')
m = tot_mkt.merge(win_mkt, on='HORA', how='left').fillna(0.0)
m['Participação (%)']=np.where(m['TOT']>0, m['WIN']/m['TOT']*100, np.nan); m['Série']='Melhor Preço'
out.append(m[['HORA','Participação (%)','Série']])
for ag in [a for a in ['123MILHAS','MAXMILHAS'] if a in dpa['Agência/Companhia'].unique()]:
    tot = dpa[dpa['Agência/Companhia']==ag].groupby('HORA').size().reset_index(name='TOT')
    win = dpa[(dpa['Agência/Companhia']==ag)&(dpa['RANKING']==1)].groupby('HORA').size().reset_index(name='WIN')
    x = tot.merge(win, on='HORA', how='left').fillna(0.0)
    x['Participação (%)']=np.where(x['TOT']>0, x['WIN']/x['TOT']*100, np.nan)
    x['Série']=ag; out.append(x[['HORA','Participação (%)','Série']])
dfp = pd.concat(out, ignore_index=True)
cmapP = build_blue_gray_map(dfp['Série'].unique())
fp = line_fig(dfp, 'HORA', 'Participação (%)', 'Série',
              "% de Ranking 1 dentro da Agência (por hora)", percent=True, cmap=cmapP)
st.plotly_chart(fp, use_container_width=True)

st.subheader("6.10 Participação (%) por Ranking – dentro do Ranking (coluna) — por hora")
dcol = dhr[dhr['RANKING']==1]
if not dcol.empty:
    cnt = dcol.groupby(['HORA','Agência/Companhia']).size().reset_index(name='Q')
    tot = cnt.groupby('HORA')['Q'].sum().reset_index(name='TOT')
    share = cnt.merge(tot, on='HORA'); share['Participação (%)']=np.where(share['TOT']>0, share['Q']/share['TOT']*100, np.nan)
    share['Série'] = share['Agência/Companhia'].replace({'123MILHAS':'123MILHAS','MAXMILHAS':'MAXMILHAS'})
    share = share[share['Série'].isin(['123MILHAS','MAXMILHAS'])]
    if not share.empty:
        cmapC = build_blue_gray_map(share['Série'].unique())
        fc = line_fig(share, 'HORA', 'Participação (%)', 'Série',
                      "Participação no Ranking 1 por hora (dentro do Ranking)", percent=True, cmap=cmapC)
        st.plotly_chart(fc, use_container_width=True)
    else:
        st.info("Sem dados para 123/MAX no Ranking 1.")
else:
    st.info("Sem dados no Ranking 1 por hora.")

render_footer(df)
