import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import altair as alt

# --- CONFIGURAÇÃO ---
st.set_page_config(
    page_title="FleetX", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

DB_MULTAS = {
    "7455-0": {"grav": "Média", "pts": 4, "val": 130.16, "desc": "Até 20% acima"},
    "7463-0": {"grav": "Grave", "pts": 5, "val": 195.23, "desc": "20% a 50% acima"},
    "5010-0": {"grav": "Gravíssima", "pts": 7, "val": 880.41, "desc": "Sem CNH/Vencida"}
}

def ger_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
        km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base', tipo_frota TEXT, 
        documento TEXT, arquivo_crlv BLOB, locadora_nome TEXT, data_locacao TEXT, data_devolucao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, 
        custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT, aprovado_por TEXT, data_aprovacao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, data TEXT, endereco TEXT, 
        codigo TEXT, gravidade TEXT, pontos INTEGER, valor REAL, descricao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT, arquivo_cnh BLOB, arquivo_termo BLOB)""")
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)""")
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (ger_hash("admin123"),))
    conn.commit()
    return conn

conn = init_db()

# --- SESSÃO E LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
    st.session_state['u_log'] = ""
    st.session_state['p_log'] = ""

if not st.session_state['auth']:
    st.title("🔑 FleetX - Login")
    with st.form("f_login"):
        u = st.text_input("ID").strip().lower()
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            res = conn.cursor().execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (u, ger_hash(s))).fetchone()
            if res:
                st.session_state['auth'] = True
                st.session_state['u_log'] = u
                st.session_state['p_log'] = res[0]
                st.rerun()
            else: st.error("Incorreto! admin / admin123")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("FleetX Control")
st.sidebar.markdown(f"👤 `{st.session_state['u_log']}` | 🛡️ `{st.session_state['p_log']}`")

try:
    dt_cnh = conn.cursor().execute("SELECT nome, cnh_vencimento FROM motoristas").fetchall()
    for n, v in dt_cnh:
        dias = (datetime.strptime(v, "%Y-%m-%d").date() - date.today()).days
        if dias
