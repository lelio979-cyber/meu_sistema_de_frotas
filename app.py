import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="SGF-Pro V29", layout="wide")

# --- CONEXÃO E ESTRUTURA ---
def get_conn():
    return sqlite3.connect('frotas_v29.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, marca TEXT, ano INTEGER, 
        chassi TEXT, renavam TEXT, km_atual INTEGER, status TEXT, 
        data_revisao DATE, foto_path TEXT, doc_path TEXT)""")
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- DASHBOARD ROBUSTO ---
def exibir_dashboard():
    st.title("📊 Painel de Gestão de Frota")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()

    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Frota", len(df))
        c2.metric("Em Manutenção", len(df[df['status'] == 'Manutenção']))
        c3.metric("KM Médio", f"{df['km_atual'].mean():.0f} km")
        c4.metric("Ativos", len(df[df['status'] == 'Ativo']))
        
        st.divider()
        st.subheader("Análise por Status")
        st.bar_chart(df['status'].value_counts())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado disponível. Realize um cadastro.")

# --- CADASTRO ROBUSTO ---
def exibir_cadastro():
    st.title("➕ Cadastro Técnico de Ativo")
    with st.form("form_robusto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            placa = st.text_input("Placa").upper()
            modelo = st.text_input("Modelo")
            marca = st.text_input("Marca")
            chassi = st.text_input("Chassi")
            renavam = st.text_input("Renavam")
        with col2:
            ano = st.number_input("Ano", 1990, 2030)
            km = st.number_input("KM Atual", 0)
            status = st.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
            rev = st.date_input("Próxima Revisão")
            foto = st.file_uploader("Foto do Veículo")
        
        if st.form_submit_button("Registrar Ativo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (placa, modelo, marca, ano, chassi, renavam, km, status, rev, str(foto), None))
            conn.commit()
            conn.close()
            st.success("Veículo cadastrado com sucesso!")

# --- FLUXO PRINCIPAL ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = get_conn()
        user = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        if user:
            st.session_state['logado'] = True; st.session_state['perfil'] = user[0]; st.rerun()
else:
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])
    if menu == "Dashboard": exibir_dashboard()
    elif menu == "Cadastro": exibir_cadastro()
