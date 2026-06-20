import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Fleet Profissional", layout="wide")
DB_NAME = "sgf_fleet_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Ativos
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, 
        status TEXT, km_atual INTEGER)""")
    # Ordens de Serviço (Manutenção/Custos)
    conn.execute("""CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, 
        servico TEXT, custo REAL, data DATE, status_os TEXT)""")
    conn.commit()
    conn.close()

init_db()

# --- MÓDULO DE GESTÃO ---
def gestao_frota():
    st.title("🚛 Gestão de Ativos")
    with st.form("form_veic"):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        motorista = col1.text_input("Motorista")
        status = col2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        km = col1.number_input("KM Atual", min_value=0)
        
        if st.form_submit_button("Salvar Veículo"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?)", 
                         (placa, modelo, motorista, status, km))
            conn.commit(); conn.close()
            st.success("Veículo atualizado!")

# --- MÓDULO ORDEM DE SERVIÇO ---
def ordem_servico():
    st.title("🛠️ Nova Ordem de Serviço")
    conn = sqlite3.connect(DB_NAME)
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)['placa'].tolist()
    
    with st.form("form_os"):
        placa = st.selectbox("Selecione o Veículo", veiculos)
        servico = st.text_input("Descrição do Serviço")
        custo = st.number_input("Custo do Serviço (R$)", min_value=0.0)
        data = st.date_input("Data da OS")
        
        if st.form_submit_button("Abrir Ordem de Serviço"):
            conn.execute("INSERT INTO os (placa, servico, custo, data, status_os) VALUES (?,?,?,?,?)", 
                         (placa, servico, custo, data, "Concluído"))
            conn.commit()
            st.success("OS registrada com sucesso!")
    conn.close()

# --- DASHBOARD DE INTELIGÊNCIA ---
def dashboard():
    st.title("📊 Fleet Intelligence")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Frota Ativa", len(df_v[df_v['status']=='Ativo']))
    c2.metric("Total Gasto (Manutenção)", f"R$ {df_os['custo'].sum():,.2f}")
    c3.metric("OS Abertas", len(df_os))
    
    st.subheader("Histórico de Manutenções")
    st.dataframe(df_os, use_container_width=True)

# --- MENU NAVEGAÇÃO ---
st.sidebar.title("SGF-Fleet Menu")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota", "Abrir OS"])

if menu == "Dashboard": dashboard()
elif menu == "Gestão de Frota": gestao_frota()
elif menu == "Abrir OS": ordem_servico()
