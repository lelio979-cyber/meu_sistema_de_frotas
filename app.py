import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro V28", layout="wide")

def get_conn():
    return sqlite3.connect('frotas_v28.db', check_same_thread=False)

# --- INICIALIZAÇÃO SEGURA ---
def init_db():
    conn = get_conn()
    # Criar tabelas
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, marca TEXT, status TEXT)")
    
    # Inserir padrão
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('user', '123', 'operador')")
    conn.commit()
    conn.close()

init_db()

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.title("🔐 Login SGF-Pro V28")
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
            st.error("Dados incorretos.")
    st.stop()

# --- DASHBOARD E MÓDULOS ---
st.sidebar.title(f"Perfil: {st.session_state['perfil']}")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])

if menu == "Dashboard":
    st.title("📊 Painel Analítico")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total de Veículos", len(df))
        st.bar_chart(df['marca'].value_counts() if 'marca' in df.columns else None)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum veículo cadastrado.")

elif menu == "Cadastro":
    if st.session_state['perfil'] != 'admin':
        st.error("Acesso restrito a administradores.")
    else:
        st.title("➕ Cadastro de Veículos")
        with st.form("form_cad"):
            p = st.text_input("Placa").upper()
            m = st.text_input("Modelo")
            ma = st.text_input("Marca")
            st_val = st.selectbox("Status", ["Ativo", "Manutenção"])
            if st.form_submit_button("Salvar"):
                conn = get_conn()
                conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?)", (p, m, ma, st_val))
                conn.commit()
                conn.close()
                st.success("Veículo salvo!")
