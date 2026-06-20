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
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        valor_locacao REAL, usuario TEXT, 
        cidade TEXT, doc_path TEXT, foto_path TEXT)""")
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
    st.title("📊 Painel Estratégico de Frota")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_d = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    
    # 1. LINHA DE KPIs (Indicadores Rápidos)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Custo Total", f"R$ {df_d['valor'].sum():,.2f}")
    c2.metric("Frota Ativa", f"{len(df_v[df_v['status']=='Ativo'])}", delta=f"{len(df_v)} Total")
    c3.metric("Ticket Médio/Veíc", f"R$ {df_d['valor'].sum()/len(df_v) if not df_v.empty else 0:,.2f}")
    c4.metric("Manutenções", f"{len(df_v[df_v['status']=='Manutenção'])}")
    
    st.markdown("---")
    
    # 2. SEÇÃO DE ANÁLISES (Layout Grid)
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Tendência de Custos por Categoria")
        if not df_d.empty:
            fig = px.bar(df_d, x='data', y='valor', color='categoria', barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aguardando lançamentos de despesas.")

    with col_right:
        st.subheader("Status dos Ativos")
        if not df_v.empty:
            fig = px.pie(df_v, names='status', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        
    # 3. MESA DE APOIO (Alertas e Detalhes)
    st.subheader("Alertas de Operação e Logística")
    if not df_v.empty:
        # Filtra veículos com km alto ou vencimento (exemplo lógico)
        st.dataframe(df_v[['placa', 'modelo', 'cidade', 'status', 'data_devolucao']], use_container_width=True)
    
    #

# --- CADASTRO ---
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
        
        if st.form_submit_button("Salvar Ativo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, marca, modelo, status, combustivel, km_inicial, data_aquisicao, valor_locacao, usuario, cidade) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (placa, marca, modelo, status, comb, km, dt_aq, valor, user, cidade))
            conn.commit()
            conn.close()
            st.success("Ativo registrado!")

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Lançar Custo"])
if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()

# --- NAVEGAÇÃO (Barra lateral) ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Lançar Custo"])
if st.sidebar.button("Sair"): st.session_state['logado'] = False; st.rerun()

if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()
elif menu == "Lançar Custo": lancar_custo()
