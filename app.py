import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")

def get_db():
    return sqlite3.connect("sgf_fleet_elite.db")

def setup_db():
    conn = get_db()
    # Tabelas Core
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, permissao TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, limite_revisao INTEGER, crlv TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, status TEXT, aprovado BOOLEAN DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, acao TEXT, tabela TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

setup_db()

# --- SEGURANÇA E SESSÃO ---
if "user" not in st.session_state: st.session_state.user = None

def login():
    st.title("🚛 SGF-Fleet Elite - Login")
    login_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Verificação simples (expandir conforme necessidade)
        st.session_state.user = {"login": login_input, "perm": "admin"}
        st.rerun()

if not st.session_state.user:
    login()
    st.stop()

# --- NAVEGAÇÃO ---
st.sidebar.title(f"Usuário: {st.session_state.user['login']}")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Manutenção", "Auditoria"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Dashboard Executivo")
    df = pd.read_sql("SELECT * FROM veiculos", get_db())
    if not df.empty:
        st.metric("Frota Ativa", len(df))
        st.dataframe(df)
    
# --- CADASTRO ---
elif menu == "Cadastro":
    st.title("📝 Gestão de Veículos")
    with st.form("cad_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Atual", 0)
        crlv = st.text_input("CRLV")
        if st.form_submit_button("Salvar"):
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?)", (placa, modelo, km, 10000, crlv))
            conn.commit()
            conn.execute("INSERT INTO logs (usuario, acao, tabela) VALUES (?,?,?)", (st.session_state.user['login'], f"Cadastrou {placa}", "veiculos"))
            conn.commit()
            conn.close()
            st.success("Veículo salvo!")

# --- MANUTENÇÃO (OS) ---
elif menu == "Manutenção":
    st.title("🛠️ Módulo de Manutenção (OS)")
    placas = pd.read_sql("SELECT placa FROM veiculos", get_db())['placa'].tolist()
    with st.form("os_form"):
        placa = st.selectbox("Veículo", placas)
        servico = st.text_input("Serviço")
        custo = st.number_input("Custo Estimado")
        if st.form_submit_button("Abrir OS"):
            conn = get_db()
            conn.execute("INSERT INTO manutencao (placa, servico, custo, status) VALUES (?,?,?,?)", (placa, servico, custo, "Pendente"))
            conn.commit()
            conn.close()
            st.success("OS Aberta para aprovação!")

# --- AUDITORIA ---
elif menu == "Auditoria":
    st.title("📜 Logs do Sistema")
    df_logs = pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", get_db())
    st.dataframe(df_logs)
