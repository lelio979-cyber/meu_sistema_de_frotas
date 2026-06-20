import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Corporativo", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        valor_locacao REAL, usuario TEXT, cidade TEXT, crlv_path TEXT, vencimento_crlv DATE)""")
    
    # Migração automática para garantir o campo crlv_path
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    cols = [info[1] for info in cursor.fetchall()]
    if 'crlv_path' not in cols:
        conn.execute("ALTER TABLE veiculos ADD COLUMN crlv_path TEXT")
    # Migração para novos campos
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    cols = [info[1] for info in cursor.fetchall()]
    if 'vencimento_crlv' not in cols: conn.execute("ALTER TABLE veiculos ADD COLUMN vencimento_crlv DATE")
    conn.close()
        
    conn.execute("""CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data DATE, categoria TEXT, valor REAL)""")
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

# --- DASHBOARD ESTRATÉGICO ---
def dashboard():
    st.title("📊 Painel de Controle Corporativo")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    # 1. FILTROS DINÂMICOS
    st.sidebar.subheader("Filtros de Gestão")
    cidades = st.sidebar.multiselect("Filtrar por Cidade", df_v['cidade'].unique())
    if cidades: df_v = df_v[df_v['cidade'].isin(cidades)]
    
    # 2. ALERTAS DE VENCIMENTO
    st.subheader("⚠️ Alertas de Vencimento (Próximos 30 dias)")
    hoje = datetime.now().date()
    limite = hoje + timedelta(days=30)
    df_v['vencimento_crlv'] = pd.to_datetime(df_v['vencimento_crlv']).dt.date
    vencendo = df_v[(df_v['vencimento_crlv'] <= limite) & (df_v['vencimento_crlv'] >= hoje)]
    
    if not vencendo.empty: st.error(f"Atenção: {len(vencendo)} veículos com documentos próximos ao vencimento!")
    else: st.success("Documentação em dia.")        
    conn.close()

# --- CADASTRO COMPLETO ---
def cadastro():
    st.title("➕ Cadastro de Veículo")
    with st.form("form_completo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        marca = c2.text_input("Marca")
        modelo = c1.text_input("Modelo")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        comb = c1.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel S10", "Flex"])
        km = c2.number_input("KM Inicial", 0)
        dt_aq = c1.date_input("Data de Aquisição")
        valor = c2.number_input("Valor Locação (R$)", 0.0)
        user = c1.text_input("Usuário")
        cidade = c2.text_input("Cidade")
        crlv = c1.file_uploader("Upload CRLV", type=['pdf', 'jpg', 'png'])
        
        if st.form_submit_button("Salvar Ativo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (placa, marca, modelo, status, comb, km, dt_aq, valor, user, cidade, crlv.name if crlv else None))
            conn.commit()
            conn.close()
            st.success("Ativo registrado com CRLV!")

# --- NAVEGAÇÃO ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Lançar Custo"])
if st.sidebar.button("Sair"): st.session_state['logado'] = False; st.rerun()

if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()
elif menu == "Lançar Custo": st.write("Módulo de Custos ativo.")
