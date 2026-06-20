import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
DB_NAME = "frota_definitiva.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

# --- INICIALIZAÇÃO (Não deleta dados existentes) ---
def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, marca TEXT, chassi TEXT, 
        renavam TEXT, km_atual INTEGER, valor REAL, status TEXT, 
        data_inicio DATE, data_fim DATE, doc_nome TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)""")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.title("🔐 Login")
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = get_conn()
        perfil = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        conn.close()
        if perfil:
            st.session_state['logado'] = True; st.session_state['perfil'] = perfil[0]; st.rerun()
    st.stop()

# --- MÓDULOS DE FUNÇÃO ---
def dashboard():
    st.title("📊 Painel Analítico")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    if not df.empty:
        st.metric("Total de Ativos", len(df))
        st.dataframe(df, use_container_width=True)
    else: st.info("Frota vazia.")

def cadastro():
    st.title("➕ Gestão de Ativos")
    with st.form("form_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        modelo = c2.text_input("Modelo")
        marca = c1.text_input("Marca")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Baixado"])
        if st.form_submit_button("Salvar Ativo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, marca, status) VALUES (?,?,?,?)", (placa, modelo, marca, status))
            conn.commit()
            conn.close()
            st.success("Salvo!")

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])
if menu == "Dashboard": dashboard()
else: cadastro()
