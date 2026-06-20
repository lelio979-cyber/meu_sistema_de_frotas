import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    # Tabela Veículos com todos os campos solicitados
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        data_devolucao DATE, valor_locacao REAL, usuario TEXT, 
        cidade TEXT, doc_path TEXT, foto_path TEXT)""")
    # Tabela Despesas
    conn.execute("""CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data DATE, categoria TEXT, valor REAL)""")
    # Tabela Usuários
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)""")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- LOGIN (Funcionalidade mantida) ---
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

# --- DASHBOARD (Com métricas e gráficos) ---
def dashboard():
    st.title("📊 Dashboard Executivo - Visão Consolidada")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_d = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    
    if not df_v.empty:
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Custo Total", f"R$ {df_d['valor'].sum():,.2f}")
        c2.metric("Frota Ativa", len(df_v[df_v['status']=='Ativo']))
        c3.metric("KM Média", f"{df_v['km_inicial'].mean():.0f}")
        c4.metric("Manutenções", len(df_v[df_v['status']=='Manutenção']))
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribuição de Custos")
            fig = px.pie(df_d, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Frota por Cidade")
            st.bar_chart(df_v['cidade'].value_counts())
    else: st.info("Nenhum dado para exibir.")

# --- CADASTRO (Com todos os campos) ---
def cadastro():
    st.title("➕ Cadastro Detalhado de Veículo")
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
        foto = c1.file_uploader("Foto", type=['jpg', 'png'])
        doc = c2.file_uploader("Documento (PDF)", type=['pdf'])
        
        if st.form_submit_button("Salvar Ativo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (placa, marca, modelo, status, comb, km, dt_aq, dt_dev, valor, user, cidade, str(doc.name) if doc else None, str(foto.name) if foto else None))
            conn.commit()
            conn.close()
            st.success("Ativo registrado!")

# --- Lançar Custo ---
def lancar_custo():
    st.title("💰 Lançar Custo")
    with st.form("form_custo"):
        data = st.date_input("Data")
        cat = st.selectbox("Categoria", ["Combustível", "Manutenção", "Multas", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("Lançar"):
            conn = get_conn()
            conn.execute("INSERT INTO despesas (data, categoria, valor) VALUES (?,?,?)", (data, cat, valor))
            conn.commit()
            conn.close()
            st.success("Despesa salva!")

# --- NAVEGAÇÃO (Barra lateral) ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Lançar Custo"])
if st.sidebar.button("Sair"): st.session_state['logado'] = False; st.rerun()

if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()
elif menu == "Lançar Custo": lancar_custo()
