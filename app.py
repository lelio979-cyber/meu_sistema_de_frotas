import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO GLOBAL ---
st.set_page_config(page_title="SGF-Pro V16 - Final", layout="wide")

def init_db():
    conn = sqlite3.connect('frotas_final.db', check_same_thread=False)
    # Criar todas as tabelas necessárias
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS motoristas (nome TEXT PRIMARY KEY, cnh TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS checklists (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, km INTEGER, data TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS ordens_servico (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, descricao TEXT, custo REAL, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL, tipo_custo TEXT, data TEXT)")
    conn.commit()
    return conn

conn = init_db()

# --- 2. MÓDULOS ---
def modulo_veiculos():
    st.header("🚗 Gestão de Veículos")
    with st.form("form_v"):
        p = st.text_input("Placa").upper(); m = st.text_input("Modelo"); k = st.number_input("KM Atual", step=1)
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?)", (p, m, k))
            conn.commit(); st.success("Veículo salvo!")
    st.dataframe(pd.read_sql("SELECT * FROM veiculos", conn))

def modulo_motoristas():
    st.header("👤 Motoristas")
    with st.form("form_m"):
        n = st.text_input("Nome"); c = st.text_input("CNH")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO motoristas VALUES (?,?)", (n, c))
            conn.commit(); st.success("Motorista salvo!")
    st.dataframe(pd.read_sql("SELECT * FROM motoristas", conn))

def modulo_checklist():
    st.header("📝 Checklist de Campo")
    v = pd.read_sql("SELECT placa FROM veiculos", conn)
    m = pd.read_sql("SELECT nome FROM motoristas", conn)
    with st.form("form_c"):
        placa = st.selectbox("Veículo", v['placa'])
        mot = st.selectbox("Motorista", m['nome'])
        km = st.number_input("KM Atual", step=1)
        if st.form_submit_button("Finalizar"):
            conn.execute("INSERT INTO checklists (placa, motorista, km, data) VALUES (?,?,?,?)", (placa, mot, km, datetime.now()))
            conn.commit(); st.success("Checklist registrado!")

def modulo_os():
    st.header("🛠️ Ordens de Serviço")
    v = pd.read_sql("SELECT placa FROM veiculos", conn)
    placa = st.selectbox("Veículo", v['placa'])
    desc = st.text_area("Descrição do Serviço"); custo = st.number_input("Custo R$")
    if st.button("Abrir O.S."):
        conn.execute("INSERT INTO ordens_servico (placa, descricao, custo, status) VALUES (?,?,?,?)", (placa, desc, custo, 'Aberta'))
        conn.commit(); st.success("O.S. registrada.")
    st.dataframe(pd.read_sql("SELECT * FROM ordens_servico", conn))

def modulo_abastecimento():
    st.header("⛽ Abastecimento")
    valor = st.number_input("Valor R$"); data = st.date_input("Data")
    if st.button("Registrar"):
        conn.execute("INSERT INTO financeiro (valor, tipo_custo, data) VALUES (?,?,?)", (valor, 'Combustível', data))
        conn.commit(); st.success("Abastecimento registrado.")

def modulo_auditoria():
    st.header("📋 Auditoria de Dados")
    st.subheader("Checklists Realizados")
    st.dataframe(pd.read_sql("SELECT * FROM checklists", conn))
    st.subheader("Custos Totais")
    st.dataframe(pd.read_sql("SELECT * FROM financeiro", conn))

# --- 3. NAVEGAÇÃO PRINCIPAL ---
def main():
    st.sidebar.title("SGF-Pro V16")
    menu = st.sidebar.radio("Módulos", [
        "🚗 Veículos", "👤 Motoristas", "📝 Checklist de Campo", 
        "🛠️ Ordens de Serviço", "⛽ Abastecimento", "📋 Auditoria"
    ])
    
    if menu == "🚗 Veículos": modulo_veiculos()
    elif menu == "👤 Motoristas": modulo_motoristas()
    elif menu == "📝 Checklist de Campo": modulo_checklist()
    elif menu == "🛠️ Ordens de Serviço": modulo_os()
    elif menu == "⛽ Abastecimento": modulo_abastecimento()
    elif menu == "📋 Auditoria": modulo_auditoria()

if __name__ == "__main__":
    main()
