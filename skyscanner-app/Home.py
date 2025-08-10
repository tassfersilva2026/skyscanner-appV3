# Home.py
import streamlit as st
from common import apply_css, carregar_dados, CAMINHO_ARQUIVO, render_footer, render_logo

st.set_page_config(
    page_title="Análise de Preços Skyscanner",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_css()
render_logo()  # mostra o logo uma única vez

st.markdown("### Use o menu lateral para navegar entre as páginas.")

df = carregar_dados(CAMINHO_ARQUIVO)
if df is None or df.empty:
    st.warning("Nenhum dado carregado.")
else:
    render_footer(df)
