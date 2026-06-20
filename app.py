import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Pro Integrado", layout="wide")

def get_conn():
    return sqlite3.connect('frotas_v31.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_inicio INTEGER, km_atual INTEGER, 
        status TEXT, data_inicio DATE, data_fim DATE, doc_path TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)""")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('user', '123', 'operador')")
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.title("🔐 Login SGF-Pro")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = get_conn()
        user = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        conn.close()
        if user:
            st.session_state['logado'] = True
            st.session_state['perfil'] = user[0]
            st.rerun()
        else:
            st.error("Credenciais inválidas!")
    st.stop()

# --- MÓDULOS ---
def exibir_dashboard():
    st.title("📊 Painel Executivo")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df.empty:
        df['data_fim'] = pd.to_datetime(df['data_fim']).dt.date
        hoje = datetime.now().date()
        alertas = df[df['data_fim'] <= (hoje + pd.Timedelta(days=30))]
        
        if not alertas.empty:
            st.error(f"⚠️ {len(alertas)} contrato(s) vencendo em até 30 dias!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Frota Ativa", len(df))
        c2.metric("KM Média", f"{df['km_atual'].mean():.0f}")
        c3.metric("Contratos Críticos", len(alertas))
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum veículo cadastrado.")

def exibir_cadastro():
    st.title("➕ Cadastro e Vigência")
    if st.session_state['perfil'] != 'admin':
        st.error("Acesso restrito a administradores.")
        return
        
    with st.form("form_v31"):
        col1, col2 = st.columns(2)
        with col1:
            placa = st.text_input("Placa").upper()
            modelo = st.text_input("Modelo")
            km_in = st.number_input("KM Inicial", 0)
            data_ini = st.date_input("Início da Vigência")
        with col2:
            data_fim = st.date_input("Fim da Vigência")
            doc = st.file_uploader("Documento (PDF)", type=['pdf'])
            status = st.selectbox("Status", ["Ativo", "Manutenção", "Vencido"])
            
        if st.form_submit_button("Salvar Registro"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?)",
                         (placa, modelo, km_in, km_in, status, data_ini, data_fim, str(doc.name) if doc else None))
            conn.commit()
            conn.close()
            st.success("Registro salvo!")

# --- FLUXO DE NAVEGAÇÃO ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])
if menu == "Dashboard": exibir_dashboard()
else: exibir_cadastro()
