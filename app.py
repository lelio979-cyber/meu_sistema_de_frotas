import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Corporativo", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn(): return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    # Tabela com todos os campos necessários
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        valor_locacao REAL, usuario TEXT, cidade TEXT, crlv_path TEXT, vencimento_crlv DATE)""")
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

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Painel Estratégico de Frota")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_d = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    
    # Filtros
    st.sidebar.subheader("Filtros de Gestão")
    cidades = st.sidebar.multiselect("Filtrar por Cidade", df_v['cidade'].unique() if not df_v.empty else [])
    if cidades: df_v = df_v[df_v['cidade'].isin(cidades)]
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Custo Total", f"R$ {df_d['valor'].sum():,.2f}")
    c2.metric("Frota Ativa", len(df_v[df_v['status']=='Ativo']))
    c3.metric("Manutenções", len(df_v[df_v['status']=='Manutenção']))
    c4.metric("Total Ativos", len(df_v))
    
    # Alertas
    if not df_v.empty:
        df_v['vencimento_crlv'] = pd.to_datetime(df_v['vencimento_crlv']).dt.date
        hoje = datetime.now().date()
        vencendo = df_v[(df_v['vencimento_crlv'] <= hoje + timedelta(days=30)) & (df_v['vencimento_crlv'] >= hoje)]
        if not vencendo.empty: st.error(f"⚠️ Alerta: {len(vencendo)} veículos com CRLV vencendo em 30 dias!")
    
    # Tabela Editável
    st.subheader("Gerenciamento de Ativos")
    edited_df = st.data_editor(df_v, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Edições"):
        conn = get_conn()
        edited_df.to_sql('veiculos', conn, if_exists='replace', index=False)
        conn.close(); st.success("Dados salvos!"); st.rerun()
    
    st.download_button("Exportar Frota (CSV)", df_v.to_csv(index=False), "frota.csv", "text/csv")

def cadastro():
    st.title("➕ Cadastro Corporativo")
    with st.form("form_corp", clear_on_submit=True):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        marca = c2.text_input("Marca")
        cidade = c1.text_input("Cidade")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        venc = c1.date_input("Vencimento CRLV")
        crlv = c2.file_uploader("Upload CRLV")
        
        if st.form_submit_button("Registrar Ativo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, marca, cidade, status, vencimento_crlv, crlv_path) VALUES (?,?,?,?,?,?)",
                         (placa, marca, cidade, status, venc, crlv.name if crlv else None))
            conn.commit(); conn.close(); st.success("Ativo registrado!")

# --- NAVEGAÇÃO ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro"])
if st.sidebar.button("Sair"): st.session_state['logado'] = False; st.rerun()

if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()
