import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Pro Gestão", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    # Tabela Veículos
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, status TEXT)")
    # Tabela Despesas
    conn.execute("CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, data DATE, categoria TEXT, placa TEXT, valor REAL, descricao TEXT)")
    # Tabela Usuários
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- TELA DE LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    st.title("🔐 Acesso ao Sistema")
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
            st.error("Credenciais inválidas!")
    st.stop()

# --- BARRA LATERAL E NAVEGAÇÃO ---
st.sidebar.title(f"Bem-vindo, {st.session_state['perfil'].capitalize()}")
menu = st.sidebar.radio("Navegação Principal", ["Dashboard", "Cadastro Veículo", "Lançar Custo"])

if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

# --- FUNÇÕES DOS MÓDULOS ---

def dashboard():
    st.title("📊 Painel Executivo")
    conn = get_conn()
    df_despesas = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    
    if not df_despesas.empty:
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Custo Total", f"R$ {df_despesas['valor'].sum():,.2f}")
        c2.metric("Despesas Lançadas", len(df_despesas))
        
        # Gráficos
        st.subheader("Custos por Categoria")
        fig = px.pie(df_despesas, values='valor', names='categoria')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum custo lançado até o momento.")

def cadastro_veiculo():
    st.title("➕ Cadastro de Veículos")
    with st.form("form_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        status = st.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        if st.form_submit_button("Salvar Veículo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?)", (placa, modelo, status))
            conn.commit()
            conn.close()
            st.success(f"Veículo {placa} salvo com sucesso!")

def lancar_custo():
    st.title("💰 Lançar Custo")
    with st.form("form_custo"):
        data = st.date_input("Data")
        cat = st.selectbox("Categoria", ["Combustível", "Manutenção", "Multas", "Outros"])
        placa = st.text_input("Placa do Veículo")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("Registrar Despesa"):
            conn = get_conn()
            conn.execute("INSERT INTO despesas (data, categoria, placa, valor) VALUES (?,?,?,?)", 
                         (data, cat, placa, valor))
            conn.commit()
            conn.close()
            st.success("Despesa registrada!")

# --- EXECUÇÃO DO MENU ---
if menu == "Dashboard": dashboard()
elif menu == "Cadastro Veículo": cadastro_veiculo()
elif menu == "Lançar Custo": lancar_custo()
