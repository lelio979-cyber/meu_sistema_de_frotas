import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÕES E CONEXÃO ---
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")

def get_db():
    return sqlite3.connect("frota.db")

def registrar_log(acao, tabela):
    conn = get_db()
    conn.execute("INSERT INTO logs (acao, tabela) VALUES (?, ?)", (acao, tabela))
    conn.commit()
    conn.close()

def setup_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, ano INTEGER, renavam TEXT, seguro TEXT, km INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, acao TEXT, tabela TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

setup_db()

# --- 2. LOGIN (BLOQUEIO DE SEGURANÇA) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔒 Acesso Restrito")
    if st.text_input("Senha:", type="password") == "1234":
        if st.button("Entrar"):
            st.session_state["autenticado"] = True
            st.rerun()
    st.stop()

# --- 3. INTERFACE PRINCIPAL ---
st.title("🚛 SGF-Fleet Elite")
menu = st.sidebar.radio("Navegação", ["Cadastro", "Manutenção", "Dashboard"])

if menu == "Cadastro":
    st.subheader("Cadastrar Veículo")
    with st.form("form_cad"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Inicial", 0)
        if st.form_submit_button("Salvar"):
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, km) VALUES (?, ?, ?)", (placa, modelo, km))
            conn.commit()
            conn.close()
            registrar_log(f"Cadastro do veículo {placa}", "veiculos")
            st.success("Veículo salvo!")

elif menu == "Manutenção":
    # (Mesma lógica de manutenção de antes...)
    st.write("Módulo de Manutenção")

elif menu == "Dashboard":
    st.subheader("Painel Geral e Auditoria")
    conn = get_db()
    df_logs = pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", conn)
    conn.close()
    st.write("### 📜 Logs de Auditoria")
    st.dataframe(df_logs)
