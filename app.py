import streamlit as st
import sqlite3

# --- 1. CONFIGURAÇÃO DO BANCO (TUDO EM UM) ---
def init_db():
    conn = sqlite3.connect('frotas_v26.db', check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            login TEXT PRIMARY KEY, 
            senha TEXT, 
            perfil TEXT
        )
    """)
    # Cria usuários padrão se não existirem
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('user', '123', 'operador')")
    conn.commit()
    return conn

conn = init_db()

# --- 2. LÓGICA DE LOGIN ---
st.set_page_config(page_title="SGF-Pro")

if 'logado' not in st.session_state:
    st.session_state['logado'] = False
    st.session_state['perfil'] = None

if not st.session_state['logado']:
    st.title("🔐 Login SGF-Pro")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (usuario, senha)).fetchone()
        if user:
            st.session_state['logado'] = True
            st.session_state['perfil'] = user[0]
            st.rerun()
        else:
            st.error("Credenciais inválidas!")
else:
    # --- 3. ÁREA LOGADA ---
    st.sidebar.title(f"Perfil: {st.session_state['perfil']}")
    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()
    
    st.title("Sistema SGF-Pro")
    st.write(f"Bem-vindo, você está logado como **{st.session_state['perfil']}**.")
    
    # Restrição de Acesso
    if st.session_state['perfil'] == 'admin':
        st.success("Painel Administrativo: Cadastro disponível.")
    else:
        st.warning("Você é um operador. Acesso ao cadastro restrito.")
