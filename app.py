import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

st.set_page_config(page_title="FleetX", layout="wide")

def ger_hash(s): return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    c = conn.cursor()
    # Criando as tabelas principais de cadastro
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', km_proxima_revisao INTEGER, trecho TEXT, tipo_frota TEXT, documento TEXT, arquivo_crlv BLOB, locadora_nome TEXT, data_locacao TEXT, data_devolucao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS motoristas (nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT, arquivo_cnh BLOB, arquivo_termo BLOB)""")
    
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
            else: st.error("Incorreto!")
    st.stop()

# --- ÁREA LOGADA - SISTEMA ATIVO ---
st.sidebar.title("FleetX Control")
st.sidebar.markdown(f"👤 `{st.session_state['u_log']}` | 🛡️ `{st.session_state['p_log']}`")

menu = st.sidebar.radio("Navegação:", ["🚗 Cadastros", "📋 Visualizar Dados"])

if st.sidebar.button("🚪 Sair", type="primary", use_container_width=True):
    st.session_state['auth'] = False
    st.rerun()

# --- MÓDULO 1: CADASTROS ---
if menu == "🚗 Cadastros":
    st.title("🚗 Central de Cadastros")
    tb1, tb2 = st.tabs(["Veículo", "Motorista"])
    
    with tb1:
        st.subheader("Cadastro de Veículo")
        tf = st.selectbox("Modalidade", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        ln = st.text_input("Nome da Locadora") if tf == "Locadora" else None
        
        with st.form("f_veic", clear_on_submit=True):
            p = st.text_input("Placa (Ex: ABC1D23)").upper().strip()
            m = st.text_input("Modelo do Veículo")
            ki = st.number_input("KM Inicial", min_value=0, step=1)
            kr = st.number_input("Próxima Revisão (KM)", min_value=0, step=1)
            tr = st.text_input("Trecho/Base Operacional")
            doc = st.text_area("Observações do Documento")
            up = st.file_uploader("Upload do CRLV (PDF/Imagem)", type=["pdf", "png", "jpg"])
            
            if st.form_submit_button("Salvar Veículo"):
                if p and m:
                    try:
                        blob = up.read() if up else None
                        conn.cursor().execute("INSERT INTO veiculos VALUES (?,?,?, 'Disponível', ?,?,?,?,?,?, NULL, NULL)", (p, m, ki, kr, tr, tf, doc, blob, ln))
                        conn.commit()
                        st.success(f"Veículo {p} cadastrado com sucesso!")
                    except Exception as e:
                        st.error("Erro: Placa já cadastrada ou dados inválidos.")
                else: st.warning("Preencha Placa e Modelo!")

    with tb2:
        st.subheader("Cadastro de Motorista")
        with st.form("f_mot", clear_on_submit=True):
            nome = st.text_input("Nome Completo")
            cnh = st.text_input("Nº da CNH")
            venc = st.date_input("Vencimento da CNH")
            u_cnh = st.file_uploader("Upload da CNH Digital", type=["pdf", "png", "jpg"])
            u_ter = st.file_uploader("Upload do Termo de Uso Assinado", type=["pdf", "png", "jpg"])
            
            if st.form_submit_button("Salvar Motorista"):
                if nome and cnh:
                    try:
                        c_blob = u_cnh.read() if u_cnh else None
                        t_blob = u_ter.read() if u_ter else None
                        conn.cursor().execute("INSERT INTO motoristas VALUES (?,?,?, 'Sim', ?,?)", (nome, cnh, str(venc), c_blob, t_blob))
                        conn.commit()
                        st.success(f"Motorista {nome} cadastrado com sucesso!")
                    except: st.error("Erro ao cadastrar motorista.")
                else: st.warning("Preencha Nome e CNH!")

# --- MÓDULO 2: VISUALIZAR DADOS ---
elif menu == "📋 Visualizar Dados":
    st.title("📋 Dados Cadastros")
    t_v, t_m = st.tabs(["Frota Cadastrada", "Motoristas Cadastrados"])
    
    with t_v:
        df_v = pd.read_sql_query("SELECT placa, modelo, km_atual, status, tipo_frota, trecho FROM veiculos", conn)
        st.dataframe(df_v, use_container_width=True)
        
    with t_m:
        df_m = pd.read_sql_query("SELECT nome, cnh_numero, cnh_vencimento FROM motoristas", conn)
        st.dataframe(df_m, use_container_width=True)
