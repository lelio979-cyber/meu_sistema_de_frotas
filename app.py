import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")

def get_conn():
    return sqlite3.connect('sistema_frota.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    # Tabela de Usuários
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    
    # Tabela Robusta de Veículos
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, marca TEXT, chassi TEXT, 
        renavam TEXT, ano INTEGER, km_inicial INTEGER, km_atual INTEGER, 
        valor_compra REAL, status TEXT, data_aquisicao DATE, 
        data_inicio DATE, data_fim DATE, doc_path TEXT)""")
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.title("🔐 Login de Acesso")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Acessar"):
        conn = get_conn()
        perfil = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (user, pwd)).fetchone()
        conn.close()
        if perfil:
            st.session_state['logado'] = True
            st.session_state['perfil'] = perfil[0]
            st.rerun()
        else:
            st.error("Login ou Senha incorretos.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])

if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sem dados para exibir.")

elif menu == "Cadastro":
    st.title("➕ Novo Ativo")
    with st.form("cadastro_robusto"):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa")
        modelo = c2.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            try:
                conn = get_conn()
                conn.execute("INSERT INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
                conn.commit()
                conn.close()
                st.success("Salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")
