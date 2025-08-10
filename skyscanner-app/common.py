# common.py — híbrido (local + Cloud + env + URL)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os, re
from datetime import datetime, timedelta
from urllib.parse import urlparse

# ==================== DETECÇÃO DE CAMINHO (ROBUSTO) ====================
def _is_url(path: str) -> bool:
    if not isinstance(path, str): return False
    try:
        u = urlparse(path)
        return u.scheme in ("http", "https")
    except Exception:
        return False

def _get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return None

def _discover_data_path() -> str | None:
    # 1) secrets
    s = _get_secret("PARQUET_PATH")
    if s: return s
    # 2) env var
    env_path = os.environ.get("PARQUET_PATH")
    if env_path: return env_path
    # 3) arquivo no repo
    cand = os.path.join("data", "OFERTAS.parquet")
    if os.path.exists(cand): return cand
    # 4) raiz
    if os.path.exists("OFERTAS.parquet"): return "OFERTAS.parquet"
    # 5) caminho local legado
    old = r"C:\Users\tassiana.silva\Downloads\teste\OFERTAS.parquet"
    return old if os.path.exists(old) else None

CAMINHO_ARQUIVO = _discover_data_path()

# ==================== PALETA / ESTILO ====================
BLUES = ['#0A2A6B','#0B5FFF','#1E6BFF','#3880FF','#5A97FF','#7FADFF','#A5C3FF','#CAD9FF','#E6F0FF']
DARK_NAVY = '#0A2A6B'
PRIMARY_BLUE = '#0B5FFF'
COLOR_123 = '#003399'
COLOR_MAX = '#00B3FF'
COLOR_MELHOR = '#00F7FF'  # azul fluorescente
COLOR_INCREASING = '#1E6BFF'
COLOR_DECREASING = '#A5C3FF'

SERIES_BLUES = ['#0B5FFF', '#3880FF', '#1E6BFF', '#7FADFF']
SERIES_GRAYS = ['#4B5563', '#9CA3AF', '#6B7280', '#94A3B8']

largura_barras_precos = 0.8
chart_height = 400
chart_height_cascade = 560
ADVPS_ORDEM = [1,3,7,14,21,30,60,90]
cias_padrao = ['GOL','LATAM','AZUL','JETSMART','TAP']

def apply_css():
    st.markdown("""
    <style>
    :root{
      --sky-blue:#0B5FFF; --sky-blue-dark:#0A2A6B; --sky-blue-500:#1E6BFF;
      --sky-blue-300:#7FADFF; --sky-blue-200:#A5C3FF; --sky-blue-100:#E6F0FF;
      --text:#0f172a; --muted:#e5e7eb;
    }
    .stApp{background:#fff;color:var(--text);}
    h1,h2,h3{color:var(--sky-blue-dark)!important;}
    section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--muted);}
    section[data-testid="stSidebar"] *{color:var(--sky-blue-dark)!important;}

    /* Inputs */
    section[data-testid="stSidebar"] div[data-baseweb="select"]>div,
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stDateInput input{
      border:1px solid var(--muted); box-shadow:none;
    }

    /* Chips SEM vermelho */
    section[data-testid="stSidebar"] [data-baseweb="tag"],
    section[data-testid="stSidebar"] [class*="tagRoot"]{
      background:var(--sky-blue)!important;color:#fff!important;border-color:var(--sky-blue-dark)!important;
    }
    section[data-testid="stSidebar"] [data-baseweb="tag"] *,
    section[data-testid="stSidebar"] [class*="tagRoot"] *{
      color:#fff!important; fill:#fff!important; stroke:#fff!important;
    }

    /* Calendário e slider em tons de azul */
    div[data-baseweb="calendar"] [aria-selected="true"], div[data-baseweb="calendar"] .selected{
      background:var(--sky-blue)!important;color:#fff!important;
    }
    div[data-baseweb="calendar"] button:hover{ background:var(--sky-blue-200)!important; }
    div[data-testid="stSlider"] [data-baseweb="slider"]>div>div{ background:var(--sky-blue-100)!important; }
    div[data-testid="stSlider"] [data-baseweb="slider"]>div>div:nth-child(2){ background:var(--sky-blue)!important; }
    div[data-testid="stSlider"] [role="slider"]{
      background:#fff!important;border:3px solid var(--sky-blue)!important;
      box-shadow:0 0 0 2px rgba(11,95,255,.15)!important;
    }

    /* Alerts azuis */
    div[data-testid="stAlert"], div[data-baseweb="toast"], div[data-testid="stException"]{
      background:var(--sky-blue)!important;color:#fff!important;border:1px solid var(--sky-blue-dark)!important;
    }
    div[data-testid="stAlert"] *, div[data-baseweb="toast"] *, div[data-testid="stException"] *{color:#fff!important;}

    /* Barra top */
    .topbar{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;
      padding:.75rem 0;border-top:1px solid var(--muted);border-bottom:1px solid var(--muted);}
    .topbar .label{font-weight:700;color:var(--sky-blue-dark);}
    </style>
    """, unsafe_allow_html=True)

# === LOGO (híbrido) ===
def get_logo_path():
    cands = []
    s = _get_secret("LOGO_PATH")
    if s: cands.append(s)
    cands += ["skyscanner.png", os.path.join("assets", "skyscanner.png")]
    cands.append(r"C:\Users\tassiana.silva\OneDrive - 123 VIAGENS E TURISMO LTDA\SKYSCANNER02\CODE\skyscanner.png")
    for p in cands:
        if not p: continue
        if _is_url(p): return p
        if os.path.exists(p): return p
    return None

def render_logo(width=210):
    p = get_logo_path()
    if p: st.image(p, width=width)

# ==================== FORMATADORES ====================
def fmt_int_br(n:int) -> str:
    return f"{int(n):,}".replace(",", "¤").replace(".", ",").replace("¤", ".")

def format_data_br(ts) -> str:
    """Garante dd/mm/aaaa HH:MM."""
    if pd.isna(ts): return ""
    ts = pd.to_datetime(ts, errors='coerce')
    if pd.isna(ts): return ""
    return ts.strftime("%d/%m/%Y %H:%M")

def format_dates_in_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].apply(lambda x: format_data_br(x) if pd.notna(x) else "")
            continue
        if pd.api.types.is_period_dtype(d[c]):
            d[c] = d[c].dt.to_timestamp()
            d[c] = d[c].apply(lambda x: format_data_br(x) if pd.notna(x) else "")
            continue
        if pd.api.types.is_object_dtype(d[c]) or pd.api.types.is_string_dtype(d[c]):
            if d[c].map(lambda v: isinstance(v, (pd.Timestamp, np.datetime64, datetime))).any():
                d[c] = pd.to_datetime(d[c], errors="coerce")
                d[c] = d[c].apply(lambda x: format_data_br(x) if pd.notna(x) else "")
    return d

def theme_plotly(fig):
    fig.update_layout(
        template='plotly_white', paper_bgcolor='white', plot_bgcolor='white',
        font=dict(color=DARK_NAVY, size=14),
        legend=dict(bgcolor='rgba(255,255,255,0.85)'),
        hoverlabel=dict(bgcolor=PRIMARY_BLUE, font_color='white')
    )
    return fig

def build_color_map(categories, include_named=True):
    named={'Melhor Preço': COLOR_MELHOR,'Grupo123': PRIMARY_BLUE,'123MILHAS': COLOR_123,'MAXMILHAS': COLOR_MAX} if include_named else {}
    cmap={}; base=[c for c in BLUES if c not in named.values()]; i=0
    for c in categories:
        if c in named: cmap[c]=named[c]
        else: cmap[c]=base[i % len(base)]; i+=1
    return cmap

def build_blue_gray_map(categories):
    cats = list(categories)
    cmap = {}
    if 'Melhor Preço' in cats:
        cmap['Melhor Preço'] = COLOR_MELHOR
        cats.remove('Melhor Preço')
    b = g = 0; blue_turn = True
    for c in cats:
        if blue_turn:
            cmap[c] = SERIES_BLUES[b % len(SERIES_BLUES)]; b += 1
        else:
            cmap[c] = SERIES_GRAYS[g % len(SERIES_GRAYS)]; g += 1
        blue_turn = not blue_turn
    return cmap

def line_fig(df, x, y, color, title, percent=False, height=380, cmap=None):
    cmap = cmap or {}
    fig = px.line(df, x=x, y=y, color=color, markers=True, color_discrete_map=cmap, title=title)
    if percent: fig.update_yaxes(ticksuffix='%')
    fig.update_layout(height=height, legend_title=None, xaxis_title=None)
    return theme_plotly(fig)

def _ensure_dataframe(obj): return obj.to_frame().T if isinstance(obj,pd.Series) else obj
def _show_styled_table(df_table, fmt='{:,.0f}', cmap='Blues'):
    df_table=_ensure_dataframe(df_table)
    if df_table is None or df_table.empty or df_table.shape[1]==0:
        st.dataframe(df_table); return
    d=format_dates_in_df_for_display(df_table.copy()); d.columns=d.columns.map(str)
    st.dataframe(d.style.background_gradient(cmap=cmap).format(fmt))

# ==================== REGIÕES / TRECHOS ====================
def expand_bidirectional(pairs):
    s=set()
    for t in pairs:
        t=(t or "").strip()
        if not t: continue
        s.add(t)
        if '-' in t:
            a,b=t.split('-',1); s.add(f"{b}-{a}")
    return sorted(s)

REGIOES_RAW={
 "NORTE":["BEL-GRU","BEL-GIG","BEL-GRU","BEL-MCP","BEL-STM","BEL-FOR","BEL-MAO","BEL-REC","BEL-CWB","BEL-FLN","BEL-CNF","BEL-NVT","BEL-SDU","CKS-CNF","MAO-STM","MAO-TBT","MAO-VCP","MAO-REC","MAO-PVH","MAO-TFF","FOR-MAO"],
 "NORDESTE":["AJU-GRU","AJU-GIG","AJU-VCP","AJU-CGH","AJU-CNF","BPS-CNF","BPS-CGH","BPS-GRU","FOR-GRU","FOR-GIG","FOR-REC","FOR-VCP","FOR-SSA","GYN-MCZ","GYN-REC","GYN-VCP","GYN-SDU","JDO-VCP","MCZ-VCP","PNZ-VCP","REC-SSA","REC-VCP","REC-VIX","SSA-VCP","SSA-VIX"],
 "CENTRO-OESTE":["BSB-CGH","BSB-REC","BSB-SDU","BSB-GIG","BSB-SSA","BSB-VCP","BSB-CNF","BSB-GRU","BSB-NAT","BSB-THE","BSB-SLZ","BSB-FOR","BSB-CGB","BSB-CWB","BSB-VIX","BSB-JPA","CGB-GRU","CGR-GRU","CGR-VCP"],
 "SUDESTE":["CAC-GRU","CGH-SDU","CGH-SSA","CGH-REC","CGH-CNF","CGH-CWB","CGH-POA","CGH-FLN","CGH-GYN","CGH-NVT","CGH-FOR","CGH-MCZ","CGH-VIX","CGH-GIG","CGH-THE","CGH-JPA","CGH-NAT","CGH-CGR","CNF-SSA","CNF-GIG","CNF-GRU","CNF-REC","CNF-FOR","CNF-SLZ","CNF-MAO","CNF-CWB","CNF-FLN","CNF-VCP","CNF-SLZ","CNF-MCZ","CNF-NAT","CNF-VIX","CNF-POA","CNF-THE"],
 "SUL":["CWB-GIG","CWB-MAO","CWB-SSA","CWB-POA","CWB-IGU","CWB-REC","CWB-SDU","FLN-GIG","FLN-SDU","FLN-MAO","FLN-SSA"]
}
REGIOES_TRECHOS={k:expand_bidirectional(v) for k,v in REGIOES_RAW.items()}

def normalize_trecho(value:str)->str:
    if value is None: return ""
    s=str(value).upper().strip().replace('—','-').replace('–','-').replace('/','-')
    s=re.sub(r'\s+','',s)
    m=re.findall(r'[A-Z]{3}',s)
    if len(m)>=2: return f"{m[0]}-{m[1]}"
    s=re.sub(r'[^A-Z]','-',s); s=re.sub(r'-+','-',s).strip('-'); return s

def normalize_set(items): return {normalize_trecho(x) for x in items}
REGIOES_TRECHOS_STD={k:normalize_set(v) for k,v in REGIOES_TRECHOS.items()}

# ==================== CARGA DE DADOS (HÍBRIDA) ====================
@st.cache_data
def carregar_dados(caminho: str | None):
    if not caminho:
        st.error("Caminho do arquivo não definido. Configure PARQUET_PATH (secret/env) ou coloque data/OFERTAS.parquet no repo.")
        return None
    try:
        if _is_url(caminho):
            df = pd.read_parquet(caminho)
        else:
            if not os.path.exists(caminho):
                st.error(f"Arquivo não encontrado: {caminho}")
                return None
            df = pd.read_parquet(caminho)

        expected=['Nome do Arquivo','Companhia Aérea','Horário1','Horário2','Horário3','Tipo de Voo','Data do Voo','Data/Hora da Busca','Agência/Companhia','Preço','TRECHO','ADVP','RANKING']
        if df.shape[1] < len(expected):
            st.error(f"O arquivo tem {df.shape[1]} colunas, esperado ≥ {len(expected)} (A..M).")
            return None
        new_cols=list(df.columns)
        for i,n in enumerate(expected): new_cols[i]=n
        df.columns=new_cols

        for c in ['Data/Hora da Busca','Data do Voo','Horário1','Horário2','Horário3']:
            if c in df.columns and not pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c]=pd.to_datetime(df[c], errors='coerce', dayfirst=True)
            elif c in df.columns:
                df[c]=pd.to_datetime(df[c], errors='coerce')

        for c in ['Preço','ADVP','RANKING']:
            if c in df.columns: df[c]=pd.to_numeric(df[c], errors='coerce')

        if 'TRECHO' in df.columns: df['TRECHO_STD']=df['TRECHO'].map(normalize_trecho)
        return df

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# ==================== FILTROS (REUTILIZÁVEIS) ====================
def get_sidebar_filters(df):
    st.sidebar.header("Filtros")
    st.sidebar.subheader("Filtro por Região")

    regiao_sel=st.sidebar.selectbox("Região", ['Todas']+list(REGIOES_TRECHOS_STD.keys()), index=0)
    df_regiao=df.copy()
    if regiao_sel!='Todas':
        df_regiao=df_regiao[df_regiao['TRECHO_STD'].isin(REGIOES_TRECHOS_STD[regiao_sel])]

    if regiao_sel=='Todas':
        trechos_disp=sorted(df_regiao['TRECHO'].dropna().unique())
    else:
        std_set=REGIOES_TRECHOS_STD[regiao_sel]
        trechos_disp=sorted(df_regiao.loc[df_regiao['TRECHO_STD'].isin(std_set),'TRECHO'].dropna().unique())
        if not trechos_disp: trechos_disp=sorted(list(REGIOES_TRECHOS[regiao_sel]))

    st.sidebar.subheader("Análise 123/Max")
    config_123_max_filtro=st.sidebar.selectbox("Como analisar 123MILHAS e MAXMILHAS?", ("Separado","Grupo123"))
    st.sidebar.markdown("---")

    tipo_agencia_filtro=st.sidebar.selectbox("Filtro de Agências/Cias", ("Geral","Agências","Cias"))
    agencias=[a for a in df_regiao['Agência/Companhia'].dropna().unique() if a not in cias_padrao]

    if tipo_agencia_filtro=='Agências':
        todas_agencias=sorted(agencias)
    elif tipo_agencia_filtro=='Cias':
        base=cias_padrao.copy()
        for a in ['123MILHAS','MAXMILHAS']:
            if a in df_regiao['Agência/Companhia'].dropna().unique(): base.append(a)
        todas_agencias=sorted(base)
    else:
        todas_agencias=sorted(df_regiao['Agência/Companhia'].dropna().unique())

    principais_default=[x for x in ['123MILHAS','MAXMILHAS'] if x in todas_agencias]
    agencias_principais=st.sidebar.multiselect("Agência(s) Principal(is)", todas_agencias, default=principais_default)
    concorrentes_pool=[a for a in todas_agencias if a not in agencias_principais]
    agencias_concorrentes=st.sidebar.multiselect("Agência(s) Concorrente(s)", ['Todos']+concorrentes_pool, default=['Todos'])
    agencias_para_analise=agencias_principais + (concorrentes_pool if 'Todos' in agencias_concorrentes else agencias_concorrentes)

    trecho_sel=st.sidebar.selectbox("Trecho", ['Todos os Trechos']+trechos_disp)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtro por ADVP")
    if df_regiao.empty or df_regiao['ADVP'].dropna().empty:
        advp_min,advp_max=0,1
    else:
        advp_min,advp_max=int(df_regiao['ADVP'].min()), int(df_regiao['ADVP'].max())
    range_default=(advp_min,advp_max) if advp_min<advp_max else (advp_min,advp_min+1)
    advp_valor=st.sidebar.selectbox('Valor fixo de ADVP', options=['Todos']+ADVPS_ORDEM, index=0)
    advp_range=st.sidebar.slider('Ou intervalo de ADVP', min_value=advp_min, max_value=max(advp_max,advp_min+1), value=range_default)

    st.sidebar.markdown("---")
    st.sidebar.header("Filtros de Data")
    df_dt=df_regiao.dropna(subset=['Data/Hora da Busca'])
    if not df_dt.empty:
        dmin,dmax=df_dt['Data/Hora da Busca'].min().date(), df_dt['Data/Hora da Busca'].max().date()
    else:
        dmin=dmax=datetime.now().date()
    periodo=st.sidebar.selectbox('Período', ('Últimos 7 dias','Últimos 15 dias','Últimos 30 dias','Período Personalizado'))
    if periodo=='Últimos 7 dias': start_default=max(dmax - timedelta(days=7), dmin)
    elif periodo=='Últimos 15 dias': start_default=max(dmax - timedelta(days=15), dmin)
    elif periodo=='Últimos 30 dias': start_default=max(dmax - timedelta(days=30), dmin)
    else: start_default=dmin
    datas_sel=st.sidebar.date_input('Intervalo de datas', value=(start_default, dmax), min_value=dmin, max_value=dmax)

    df_filtrado=df_regiao.copy()
    if tipo_agencia_filtro=='Agências':
        df_filtrado=df_filtrado[~df_filtrado['Agência/Companhia'].isin(cias_padrao)]
    elif tipo_agencia_filtro=='Cias':
        df_filtrado=df_filtrado[df_filtrado['Agência/Companhia'].isin(cias_padrao+['123MILHAS','MAXMILHAS'])]

    if config_123_max_filtro=='Grupo123':
        df_filtrado=df_filtrado.copy()
        df_filtrado['Agência/Companhia']=df_filtrado['Agência/Companhia'].replace(['123MILHAS','MAXMILHAS'],'Grupo123')

    if advp_valor!='Todos':
        df_filtrado=df_filtrado[df_filtrado['ADVP']==advp_valor]
    else:
        df_filtrado=df_filtrado[(df_filtrado['ADVP']>=advp_range[0])&(df_filtrado['ADVP']<=advp_range[1])]

    df_filtrado=df_filtrado[df_filtrado['Agência/Companhia'].isin(agencias_para_analise)]

    if len(datas_sel)==2:
        sd,ed=pd.to_datetime(datas_sel[0]),pd.to_datetime(datas_sel[1])
        df_filtrado=df_filtrado[(df_filtrado['Data/Hora da Busca'].dt.date>=sd.date())&(df_filtrado['Data/Hora da Busca'].dt.date<=ed.date())]

    if trecho_sel!='Todos os Trechos':
        df_filtrado=df_filtrado[df_filtrado['TRECHO']==trecho_sel]

    return dict(
        regiao_sel=regiao_sel, tipo_agencia_filtro=tipo_agencia_filtro, config_123_max_filtro=config_123_max_filtro,
        agencias_principais=agencias_principais, agencias_para_analise=agencias_para_analise,
        trecho_sel=trecho_sel, advp_valor=advp_valor, advp_range=advp_range, datas_sel=datas_sel,
        df_regiao=df_regiao, df_filtrado=df_filtrado
    )

# Mantém 123 e MAX separados (para timeseries e análises específicas)
def apply_filters_for_timeseries(df_regiao, tipo_agencia_filtro, advp_valor, advp_range,
                                 datas_sel, trecho_sel, agencias_para_analise):
    d = df_regiao.copy()
    if tipo_agencia_filtro=='Agências':
        d = d[~d['Agência/Companhia'].isin(cias_padrao)]
    elif tipo_agencia_filtro=='Cias':
        d = d[d['Agência/Companhia'].isin(cias_padrao+['123MILHAS','MAXMILHAS'])]

    if advp_valor!='Todos':
        d = d[d['ADVP']==advp_valor]
    else:
        d = d[(d['ADVP']>=advp_range[0])&(d['ADVP']<=advp_range[1])]

    if len(datas_sel)==2:
        sd,ed=pd.to_datetime(datas_sel[0]),pd.to_datetime(datas_sel[1])
        d = d[(d['Data/Hora da Busca'].dt.date>=sd.date())&(d['Data/Hora da Busca'].dt.date<=ed.date())]

    if trecho_sel!='Todos os Trechos':
        d = d[d['TRECHO']==trecho_sel]

    alvo = set(agencias_para_analise) | {'123MILHAS','MAXMILHAS'}
    d = d[d['Agência/Companhia'].isin([x for x in d['Agência/Companhia'].unique() if x in alvo])]
    return d

def add_period_column(df: pd.DataFrame, modo: str, sd, ed) -> pd.DataFrame:
    """Agrega por período (Semanal/Quinzenal/Mensal) obedecendo ao intervalo do filtro."""
    d = df.dropna(subset=['Data/Hora da Busca']).copy()
    dt = d['Data/Hora da Busca'].dt.floor('D')

    sd = pd.to_datetime(sd).normalize()
    ed = pd.to_datetime(ed).normalize()
    step = 7 if modo == 'Semanal' else (15 if modo == 'Quinzenal' else 30)

    mask = (dt >= sd) & (dt <= ed)
    d = d.loc[mask].copy()
    dt = d['Data/Hora da Busca'].dt.floor('D')

    offset_days = (dt - sd).dt.days
    idx = (offset_days // step).clip(lower=0)

    bin_start = sd + pd.to_timedelta(idx * step, unit='D')
    bin_end   = bin_start + pd.to_timedelta(step - 1, unit='D')
    d['PERIODO'] = np.where(bin_end <= ed, bin_end, ed)
    d['PERIODO'] = pd.to_datetime(d['PERIODO']).dt.normalize()
    return d

def render_footer(df):
    st.markdown("---")
    ultima_raw = df['Data/Hora da Busca'].max() if 'Data/Hora da Busca' in df.columns else None
    # Buscas: por Nome do Arquivo (se existir) senão por timestamp arredondado
    if 'Nome do Arquivo' in df.columns and df['Nome do Arquivo'].notna().any():
        qtd_buscas = int(df['Nome do Arquivo'].nunique())
    elif 'Data/Hora da Busca' in df.columns:
        qtd_buscas = int(df['Data/Hora da Busca'].dt.floor('min').nunique())
    else:
        qtd_buscas = 0
    qtd_ofertas = int(len(df))
    if pd.notna(ultima_raw):
        st.caption(
            f"Última atualização do banco: **{format_data_br(ultima_raw)}** • "
            f"Buscas: **{fmt_int_br(qtd_buscas)}** • Ofertas: **{fmt_int_br(qtd_ofertas)}**"
        )
    else:
        st.caption(f"Buscas: **{fmt_int_br(qtd_buscas)}** • Ofertas: **{fmt_int_br(qtd_ofertas)}**")
