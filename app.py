import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    # Cria a tabela se não existir
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        data_devolucao DATE, valor_locacao REAL, usuario TEXT, 
        cidade TEXT, doc_path TEXT, foto_path TEXT)""")
    
    # Migração automática para garantir que todos os campos existam
    colunas_atuais = [info[1] for info in conn.execute("PRAGMA table_info(veiculos)").fetchall()]
    campos = {'doc_path': 'TEXT', 'foto_path': 'TEXT'}
    for col, tipo in campos.items():
        if col not in colunas_atuais:
            conn.execute(f"ALTER TABLE veiculos ADD COLUMN {col} {tipo}")
            
    conn.execute("""CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data DATE, categoria TEXT, valor REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)""")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.title("🔐 Login SGF-Pro")
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = get_conn()
        perfil = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        conn.close()
        if perfil:
            st.session_state['logado'] = True; st.session_state['perfil'] = perfil[0]; st.rerun()
    st.stop()

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Dashboard Executivo")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_d = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    
    if not df_v.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Frota Ativa", len(df_v[df_v['status']=='Ativo']))
        col2.metric("Custo Mensal", f"R$ {df_d['valor'].sum():,.2f}")
        col3.metric("Total Veículos", len(df_v))
        
        st.divider()
        fig = px.pie(df_v, names='status', title="Distribuição de Status")
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Nenhum veículo cadastrado.")

def cadastro():
    st.title("➕ Cadastro Completo")
    with st.form("form_completo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        marca = c2.text_input("Marca")
        modelo = c1.text_input("Modelo")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        comb = c1.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel S10", "Flex"])
        km = c2.number_input("KM Inicial", 0)
        dt_aq = c1.date_input("Data de Aquisição")
        dt_dev = c2.date_input("Data de Devolução")
        valor = c1.number_input("Valor Locação (R$)", 0.0)
        user = c2.text_input("Usuário")
        cidade = c1.text_input("Cidade")
        foto = c1.file_uploader("Foto do Veículo", type=['jpg', 'png'])
        doc = c2.file_uploader("Documento (PDF)", type=['pdf'])
        
        if st.form_submit_button("Salvar Registro"):
            conn = get_conn()
            conn.execute("""INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (placa, marca, modelo, status, comb, km, dt_aq, dt_dev, valor, user, cidade, str(doc.name) if doc else None, str(foto.name) if foto else None))
            conn.commit()
            conn.close()
            st.success("Dados salvos com sucesso!")

# --- NAVEGAÇÃO ---
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Lançar Custo"])
if st.sidebar.button("Sair"): st.session_state['logado'] = False; st.rerun()

if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()
