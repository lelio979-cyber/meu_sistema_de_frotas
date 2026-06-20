import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SGF-Pro Executivo", layout="wide")

def get_conn():
    return sqlite3.connect('frota_executiva.db', check_same_thread=False)

# --- INICIALIZAÇÃO DE DADOS (Simulando o seu Dashboard) ---
def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS frota (
        id INTEGER PRIMARY KEY, categoria TEXT, valor REAL, 
        status TEXT, combustivel_tipo TEXT, litros REAL)""")
    # Populando dados de exemplo baseados na sua imagem
    if conn.execute("SELECT count(*) FROM frota").fetchone()[0] == 0:
        dados = [('Combustível', 10756.13, 'Ativo', 'Gasolina', 2495.25),
                 ('Manutenção', 70263.79, 'Manutenção', 'Etanol', 415.47)]
        conn.executemany("INSERT INTO frota (categoria, valor, status, combustivel_tipo, litros) VALUES (?,?,?,?,?)", dados)
        conn.commit()
    conn.close()

init_db()

# --- DASHBOARD EXECUTIVO ---
st.title("🚛 Dashboard Executivo - Gestão de Frotas")

conn = get_conn()
df = pd.read_sql("SELECT * FROM frota", conn)
conn.close()

# 1. Linha de KPIs (Indicadores)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Custo Total Mensal", f"R$ {df['valor'].sum():,.2f}")
c2.metric("Frota Ativa", "89 / 125")
c3.metric("Consumo Médio", "R$ 11,57")
c4.metric("Multas Pendentes", "1")

st.divider()

# 2. Gráficos de Análise
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Distribuição de Custos")
    fig_pie = px.pie(df, values='valor', names='categoria', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_g2:
    st.subheader("Consumo por Combustível (L)")
    fig_bar = px.bar(df, x='combustivel_tipo', y='litros', color='combustivel_tipo')
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Dados Consolidados")
st.dataframe(df, use_container_width=True)
