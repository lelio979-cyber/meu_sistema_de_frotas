import streamlit as st
import sqlite3
import hashlib

st.set_page_config(page_title="FleetX", layout="wide")

def ger_hash(s): 
    return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)""")
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (ger_hash("admin123"),))
    conn.commit()
    return conn

conn = init_db()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'u_log': "", 'p_log': ""})

if not st.session_state['auth']:
    st.title("🔑 FleetX - Login")
    with st.form("f_login"):
        u = st.text_input("ID").strip().lower()
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            res = conn.cursor().execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (u, ger_hash(s))).fetchone()
            if res:
                st.session_state.update({'auth': True, 'u_log': u, 'p_log': res[0]})
                st.rerun()
            else: 
                st.error("Incorreto! Use admin / admin123")
    st.stop()

# Se passar do login, mostra isso:
st.title("🚀 FleetX - Painel Principal")
st.write(f"Bem-vindo, {st.session_state['u_log']}! A Fase 1 está funcionando.")

if st.button("🚪 Sair"):
    st.session_state['auth'] = False
    st.rerun()
