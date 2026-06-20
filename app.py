import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")

def get_db(): return sqlite3.connect("sgf_fleet_elite.db")

def registrar_log(usuario, acao, tabela):
    conn = get_db()
    conn.execute("INSERT INTO logs (usuario, acao, tabela) VALUES (?,?,?)", (usuario, acao, tabela))
    conn.commit()
    conn.close()

def setup_db():
    conn = get_db()
    # Tabelas Core
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, permissao TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, limite_revisao INTEGER, crlv TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, status TEXT, aprovado BOOLEAN DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, acao TEXT, tabela TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    
    # Criar admin padrão se não existir
    try:
        conn.execute("INSERT INTO usuarios VALUES ('admin', 'admin', 'admin')")
    except: pass
    conn.commit()
    conn.close()

setup_db()

# --- AUTENTICAÇÃO ---
if "user" not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.title("🚛 SGF-Fleet Elite - Login")
    login_in = st.text_input("Usuário")
    senha_in = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        st.session_state.user = {"login": login_in, "perm": "admin"}
        st.rerun()
    st.stop()

# --- NAVEGAÇÃO E MÓDULOS ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro", "Manutenção", "Auditoria"])

if menu == "Dashboard":
    st.title("📊 Dashboard Executivo")
    df = pd.read_sql("SELECT * FROM veiculos", get_db())
    if not df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Frota Total", len(df))
        st.dataframe(df)

elif menu == "Cadastro":
    st.title("📝 Gestão de Veículos")
    with st.form("cad_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Atual", 0)
        crlv = st.text_input("CRLV")
        if st.form_submit_button("Salvar Veículo"):
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?)", (placa, modelo, km, 10000, crlv))
            conn.commit()
            registrar_log(st.session_state.user['login'], f"Cadastrou/Editou {placa}", "veiculos")
            conn.close()
            st.success("Veículo salvo!")

elif menu == "Manutenção":
    st.title("🛠️ Fluxo de Aprovação de OS")
    
    # Abertura
    with st.expander("➕ Nova OS"):
        with st.form("os_form"):
            placa = st.selectbox("Veículo", pd.read_sql("SELECT placa FROM veiculos", get_db())['placa'])
            servico = st.text_input("Serviço")
            custo = st.number_input("Custo R$", min_value=0.0)
            if st.form_submit_button("Solicitar Aprovação"):
                conn = get_db()
                conn.execute("INSERT INTO manutencao (placa, servico, custo, status, aprovado) VALUES (?,?,?,?,?)", (placa, servico, custo, "Pendente", 0))
                conn.commit()
                registrar_log(st.session_state.user['login'], f"Solicitou OS para {placa}", "manutencao")
                conn.close()
                st.success("OS enviada!")

    # Aprovação (Simulado como Admin)
    st.subheader("📋 Pendentes de Aprovação")
    pendentes = pd.read_sql("SELECT * FROM manutencao WHERE aprovado = 0", get_db())
    for i, row in pendentes.iterrows():
        c1, c2 = st.columns([3, 1])
        c1.write(f"Veículo: {row['placa']} | Custo: R$ {row['custo']}")
        if c2.button("✅ Aprovar", key=f"btn_{row['id']}"):
            conn = get_db()
            conn.execute("UPDATE manutencao SET aprovado = 1, status = 'Concluído' WHERE id = ?", (row['id'],))
            conn.commit()
            registrar_log(st.session_state.user['login'], f"Aprovou OS #{row['id']}", "manutencao")
            conn.close()
            st.rerun()

elif menu == "Auditoria":
    st.title("📜 Auditoria de Sistema")
    st.dataframe(pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", get_db()))
