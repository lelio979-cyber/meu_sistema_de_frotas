import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO E BANCO DE DADOS ---
st.set_page_config(page_title="SGF-Fleet Enterprise", layout="wide")

def get_db():
    return sqlite3.connect("frota_enterprise.db")

def registrar_log(acao, tabela):
    conn = get_db()
    conn.execute("INSERT INTO logs (acao, tabela) VALUES (?, ?)", (acao, tabela))
    conn.commit()
    conn.close()

def setup_db():
    conn = get_db()
    # Tabela Veículos
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, limite_revisao INTEGER)""")
    # Tabela Checklist
    conn.execute("""CREATE TABLE IF NOT EXISTS checklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, status TEXT, data DATE)""")
    # Tabela Auditoria
    conn.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, acao TEXT, tabela TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

setup_db()

# --- 2. SEGURANÇA (LOGIN) ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    if st.text_input("Senha de Acesso", type="password") == "admin":
        if st.button("Entrar"):
            st.session_state.autenticado = True
            st.rerun()
    st.stop()

# --- 3. NAVEGAÇÃO E MÓDULOS ---
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Checklist"])

if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    conn = get_db()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_logs = pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC LIMIT 10", conn)
    conn.close()
    
    st.subheader("Frota Cadastrada")
    st.dataframe(df_v)
    
    st.subheader("📜 Auditoria Recente")
    st.dataframe(df_logs)

elif menu == "Cadastro":
    st.title("📝 Cadastro de Ativos")
    with st.form("form_cad"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Atual", 0)
        limite = st.number_input("KM para Revisão", 10000)
        if st.form_submit_button("Salvar Veículo"):
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?)", (placa, modelo, km, limite))
            conn.commit()
            conn.close()
            registrar_log(f"Cadastro: {placa}", "veiculos")
            st.success("Veículo salvo com sucesso!")

elif menu == "Checklist":
    st.title("✅ Checklist Operacional")
    conn = get_db()
    placas = pd.read_sql("SELECT placa FROM veiculos", conn)['placa'].tolist()
    conn.close()
    
    with st.form("form_check"):
        placa = st.selectbox("Selecione o Veículo", placas)
        status = st.selectbox("Status", ["OK", "Necessita Reparo"])
        if st.form_submit_button("Finalizar Inspeção"):
            conn = get_db()
            conn.execute("INSERT INTO checklist (placa, status, data) VALUES (?,?,?)", (placa, status, datetime.now()))
            conn.commit()
            conn.close()
            registrar_log(f"Checklist {placa}: {status}", "checklist")
            st.success("Checklist registrado!")
