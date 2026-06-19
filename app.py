import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import altair as alt

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="FleetX - Gestão Inteligente", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- DICIONÁRIO DE MULTAS ---
DICIONARIO_MULTAS = {
    "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Até 20% acima do limite"},
    "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "De 20% a 50% acima do limite"},
    "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Dirigir sem CNH ou vencida"}
}

# --- INFRAESTRUTURA DE BANCO DE DADOS ---
def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def conectar_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
        km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base Central', tipo_frota TEXT, 
        documento TEXT, arquivo_crlv BLOB, locadora_nome TEXT, data_locacao TEXT, data_devolucao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, 
        custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT, aprovado_por TEXT, data_aprovacao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, data TEXT, endereco TEXT, 
        codigo TEXT, gravidade TEXT, pontos INTEGER, valor REAL, descricao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT, arquivo_cnh BLOB, arquivo_termo BLOB)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)''')
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (gerar_hash("admin123"),))
    conn.commit()
    return conn

conn = conectar_db()

# --- SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario_logado'] = ""
    st.session_state['perfil_logado'] = ""

if not st.session_state['autenticado']:
    st.title("🔑 FleetX - Login")
    with st.form("form_login"):
        u_in = st.text_input("ID").strip().lower()
        s_in = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (u_in, gerar_hash(s_in)))
            res = cursor.fetchone()
            if res:
                st.session_state['autenticado'] = True
                st.session_state['usuario_logado'] = u_in
                st.session_state['perfil_logado'] = res[0]
                st.rerun()
            else:
                st.error("Incorreto! Use admin / admin123")
    st.stop()

# --- DADOS GLOBAIS REATIVOS ---
try:
    df_veiculos_global = pd.read_sql_query("SELECT placa FROM veiculos", conn)
except:
    df_veiculos_global = pd.DataFrame(columns=['placa'])

# --- SIDEBAR & CNH COMPLIANCE ---
st.sidebar.title("FleetX Control")
st.sidebar.markdown(f"👤 `{st.session_state['usuario_logado']}` | 🛡️ `{st.session_state['perfil_logado'].upper()}`")

try:
    df_cnh = pd.read_sql_query("SELECT nome, cnh_venc
