import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Pro ERP", layout="wide")
conn = sqlite3.connect("sgf_erp_pro.db", check_same_thread=False)
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
def init_db():
    queries = [
        "CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY, placa TEXT, modelo TEXT, status TEXT DEFAULT 'Disponível')",
        "CREATE TABLE IF NOT EXISTS abastecimento (id INTEGER PRIMARY KEY, id_veiculo INTEGER, km REAL, litros REAL, valor REAL, data TEXT)",
        "CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY, id_veiculo INTEGER, desc TEXT, custo REAL, data TEXT, aprovado TEXT)",
        "CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY, id_veiculo INTEGER, codigo TEXT, local TEXT, valor REAL, data TEXT)",
        "CREATE TABLE IF NOT EXISTS sinistros (id INTEGER PRIMARY KEY, id_veiculo INTEGER, tipo TEXT, local TEXT, detalhes TEXT, foto_path TEXT)",
        "CREATE TABLE IF NOT EXISTS checklist (id INTEGER PRIMARY KEY, id_veiculo INTEGER, pneus TEXT, luzes TEXT, status TEXT, data TEXT)",
        "CREATE TABLE IF NOT EXISTS aprovacoes (id INTEGER PRIMARY KEY, ref_id INTEGER, tipo TEXT, aprovador TEXT, data TEXT)"
    ]
    for q in queries: conn.execute(q)
    conn.commit()

init_db()

# --- FUNÇÕES CORE ---
def update_status(id_v, status):
    conn.execute("UPDATE frota SET status = ? WHERE id = ?", (status, id_v))
    conn.commit()

# --- INTERFACE ---
st.sidebar.title("🚀 SGF-Fleet Pro")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Ficha Técnica", "Cadastro/Movimentação", "Consultas"])

if menu == "Dashboard":
    st.title("📊 Painel Geral")
    df = pd.read_sql("SELECT status, count(*) as total FROM frota GROUP BY status", conn)
    fig = px.pie(df, values='total', names='status', title="Status da Frota")
    st.plotly_chart(fig, use_container_width=True)

elif menu == "Ficha Técnica":
    st.title("📋 Prontuário do Veículo")
    veiculos = pd.read_sql("SELECT * FROM frota", conn)
    id_v = st.selectbox("Selecione o Veículo", veiculos['id'], format_func=lambda x: veiculos[veiculos['id']==x]['placa'].values[0])
    
    tab1, tab2, tab3 = st.tabs(["Financeiro", "Manutenção", "Ocorrências"])
    with tab1:
        st.metric("Total Gasto", f"R$ {pd.read_sql(f'SELECT SUM(custo) FROM manutencao WHERE id_veiculo={id_v}', conn).iloc[0,0] or 0:,.2f}")
    with tab2:
        st.dataframe(pd.read_sql(f"SELECT * FROM manutencao WHERE id_veiculo={id_v}", conn))
    with tab3:
        st.subheader("Multas")
        st.dataframe(pd.read_sql(f"SELECT * FROM multas WHERE id_veiculo={id_v}", conn))
        st.subheader("Sinistros")
        st.dataframe(pd.read_sql(f"SELECT * FROM sinistros WHERE id_veiculo={id_v}", conn))

elif menu == "Cadastro/Movimentação":
    op = st.selectbox("Ação", ["Veículo", "Manutenção", "Sinistro", "Aprovação"])
    if op == "Veículo":
        with st.form("f1"):
            p, m = st.text_input("Placa"), st.text_input("Modelo")
            if st.form_submit_button("Salvar"):
                conn.execute("INSERT INTO frota (placa, modelo) VALUES (?,?)", (p, m))
                conn.commit()
    elif op == "Manutenção":
        with st.form("f2"):
            id_v, desc, custo = st.number_input("ID"), st.text_area("Desc"), st.number_input("Custo")
            if st.form_submit_button("Registrar"):
                conn.execute("INSERT INTO manutencao (id_veiculo, desc, custo, data) VALUES (?,?,?,?)", (id_v, desc, custo, datetime.now().strftime("%Y-%m-%d")))
                update_status(id_v, "Em Manutenção")
                conn.commit()

elif menu == "Consultas":
    t = st.selectbox("Tabela", ["frota", "manutencao", "multas", "sinistros"])
    st.dataframe(pd.read_sql(f"SELECT * FROM {t}", conn), use_container_width=True)
