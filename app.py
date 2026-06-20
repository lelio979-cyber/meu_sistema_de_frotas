import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Professional", layout="wide")
DB_NAME = "sgf_fleet.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Tabela Central de Ativos
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, 
        status TEXT, km_atual INTEGER, dt_venc_crlv DATE)""")
    # Tabela de Manutenção (Histórico)
    conn.execute("""CREATE TABLE IF NOT EXISTS manutencao (
        id INTEGER PRIMARY KEY, placa TEXT, data DATE, 
        servico TEXT, custo REAL)""")
    conn.commit()
    conn.close()

init_db()

# --- INTERFACE PROFISSIONAL ---
st.sidebar.title("SGF-Fleet V1")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Gestão de Frota", "Ordens de Serviço"])

def dashboard():
    st.title("📊 Painel de Controle (Fleet Intelligence)")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Ativos", len(df))
        c2.metric("Frota em Operação", len(df[df['status'] == 'Ativo']))
        c3.metric("KM Média", f"{df['km_atual'].mean():,.0f} KM")
        
        st.subheader("Status Operacional")
        st.bar_chart(df['status'].value_counts())
        st.dataframe(df, use_container_width=True)

def gestao_frota():
    st.title("🚛 Cadastro e Gestão")
    with st.form("form_veic"):
        placa = st.text_input("Placa do Veículo").upper()
        modelo = st.text_input("Modelo")
        motorista = st.text_input("Motorista Responsável")
        status = st.selectbox("Status Atual", ["Ativo", "Manutenção", "Inativo"])
        km = st.number_input("KM Atual", min_value=0)
        if st.form_submit_button("Registrar/Atualizar Ativo"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?)", 
                         (placa, modelo, motorista, status, km, "2026-12-31"))
            conn.commit(); conn.close(); st.success("Ativo registrado no SGF-Fleet!")

if menu == "Dashboard": dashboard()
elif menu == "Gestão de Frota": gestao_frota()
