import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO E BANCO DE DADOS ---
st.set_page_config(page_title="SGF-Pro V16", layout="wide")
conn = sqlite3.connect('frotas_v16.db', check_same_thread=False)

def init_db():
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, km_proxima_revisao INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS motoristas (nome TEXT PRIMARY KEY, cnh TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS checklists (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, km INTEGER, data TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS ordens_servico (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, descricao TEXT, status TEXT, custo REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, valor REAL, data TEXT, tipo_custo TEXT)")
    # Tabela de Auditoria (Sua segurança corporativa)
    conn.execute("CREATE TABLE IF NOT EXISTS logs_auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, acao TEXT, usuario TEXT, data TEXT)")
    conn.commit()

init_db()

def registrar_log(acao):
    usuario = st.session_state.get('u_log', 'Sistema')
    conn.execute("INSERT INTO logs_auditoria (acao, usuario, data) VALUES (?, ?, ?)", (acao, usuario, datetime.now()))
    conn.commit()

# --- 2. MÓDULOS MODULARIZADOS ---
def modulo_veiculos():
    st.header("🚗 Gestão de Veículos")
    with st.form("veiculo"):
        p = st.text_input("Placa").upper(); m = st.text_input("Modelo"); k = st.number_input("KM Atual", step=1)
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?)", (p, m, k, k+10000))
            conn.commit(); registrar_log(f"Cadastrou veículo {p}")
            st.success("Veículo salvo!")

def modulo_motoristas():
    st.header("👤 Motoristas")
    with st.form("mot"):
        nome = st.text_input("Nome"); cnh = st.text_input("CNH")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO motoristas VALUES (?,?)", (nome, cnh))
            conn.commit(); registrar_log(f"Cadastrou motorista {nome}")
            st.success("Motorista salvo!")
    st.dataframe(pd.read_sql("SELECT * FROM motoristas", conn))

def modulo_checklist():
    st.header("📝 Checklist de Campo")
    placa = st.selectbox("Placa", pd.read_sql("SELECT placa FROM veiculos", conn)['placa'])
    if st.button("Finalizar Inspeção"):
        conn.execute("INSERT INTO checklists (placa, data) VALUES (?,?)", (placa, datetime.now()))
        conn.commit(); registrar_log(f"Checklist em {placa}")
        st.success("Checklist concluído.")

def modulo_os():
    st.header("🛠️ Ordens de Serviço")
    placa = st.selectbox("Veículo", pd.read_sql("SELECT placa FROM veiculos", conn)['placa'])
    desc = st.text_area("Descrição"); custo = st.number_input("Custo R$")
    if st.button("Abrir O.S."):
        conn.execute("INSERT INTO ordens_servico (placa, descricao, status, custo) VALUES (?,?,?,?)", (placa, desc, 'Aberta', custo))
        conn.commit(); registrar_log(f"OS aberta para {placa}")
        st.success("O.S. registrada.")

def modulo_abastecimento():
    st.header("⛽ Abastecimento e Auditoria")
    v = st.number_input("Valor R$")
    if st.button("Registrar"):
        conn.execute("INSERT INTO financeiro (valor, tipo_custo, data) VALUES (?,?,?)", (v, 'Combustível', datetime.now()))
        conn.commit(); registrar_log("Abastecimento registrado")
        st.success("Registrado.")

def modulo_auditoria():
    st.header("📋 Auditoria Geral")
    st.subheader("Logs de Ações")
    st.dataframe(pd.read_sql("SELECT * FROM logs_auditoria ORDER BY id DESC", conn))
    st.subheader("Checklists")
    st.dataframe(pd.read_sql("SELECT * FROM checklists", conn))

# --- 3. NAVEGAÇÃO E EXECUÇÃO ---
def main():
    st.sidebar.title("Navegação SGF-Pro")
    menu = st.sidebar.radio("Módulos", [
        "🚗 Veículos", "👤 Motoristas", "📝 Checklist de Campo", 
        "🛠️ Ordens de Serviço", "⛽ Abastecimento", 
        "📋 Auditoria de Checklists"
    ])
    
    if menu == "🚗 Veículos": modulo_veiculos()
    elif menu == "👤 Motoristas": modulo_motoristas()
    elif menu == "📝 Checklist de Campo": modulo_checklist()
    elif menu == "🛠️ Ordens de Serviço": modulo_os()
    elif menu == "⛽ Abastecimento": modulo_abastecimento()
    elif menu == "📋 Auditoria de Checklists": modulo_auditoria()

if __name__ == "__main__":
    main()
