import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Corporativo", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

# --- INICIALIZAÇÃO SEGURA (Reseta estrutura em caso de erro) ---
def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, 
        marca TEXT, 
        modelo TEXT, 
        status TEXT, 
        combustivel TEXT, 
        km_inicial INTEGER, 
        data_aquisicao DATE, 
        valor_locacao REAL, 
        usuario TEXT, 
        cidade TEXT, 
        crlv_path TEXT, 
        vencimento_crlv DATE)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        data DATE, 
        categoria TEXT, 
        valor REAL)""")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.title("🔐 Login SGF-Pro")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = get_conn()
        perfil = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        conn.close()
        if perfil:
            st.session_state['logado'] = True
            st.session_state['perfil'] = perfil[0]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Painel Estratégico de Frota")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df_v.empty:
        # Filtros
        cidades = st.sidebar.multiselect("Filtrar por Cidade", df_v['cidade'].unique())
        if cidades: df_v = df_v[df_v['cidade'].isin(cidades)]
        
        # Alertas de Vencimento
        df_v['vencimento_crlv'] = pd.to_datetime(df_v['vencimento_crlv']).dt.date
        hoje = datetime.now().date()
        vencendo = df_v[(df_v['vencimento_crlv'] <= hoje + timedelta(days=30)) & (df_v['vencimento_crlv'] >= hoje)]
        if not vencendo.empty:
            st.error(f"⚠️ Atenção: {len(vencendo)} veículos com CRLV vencendo em breve!")
        
        st.subheader("Gerenciamento de Frota")
        edited_df = st.data_editor(df_v, use_container_width=True)
        if st.button("Salvar Edições"):
            conn = get_conn()
            edited_df.to_sql('veiculos', conn, if_exists='replace', index=False)
            conn.close()
            st.success("Dados salvos!")
            st.rerun()
    else:
        st.info("Nenhum veículo cadastrado.")

def cadastro():
    st.title("➕ Cadastro Corporativo")
    with st.form("form_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        marca = c2.text_input("Marca")
        cidade = c1.text_input("Cidade")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        venc = c1.date_input("Vencimento CRLV")
        
        if st.form_submit_button("Salvar Veículo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, marca, cidade, status, vencimento_crlv) VALUES (?,?,?,?,?)",
                         (placa, marca, cidade, status, venc))
            conn.commit()
            conn.close()
            st.success("Veículo cadastrado!")

# --- NAVEGAÇÃO ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

if menu == "Dashboard": dashboard()
else: cadastro()
