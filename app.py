import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")
DB_NAME = "sgf_fleet_elite.db"

# --- BANCO DE DADOS ATUALIZADO ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, km_atual INTEGER, km_revisao INTEGER, custo_acumulado REAL DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, data DATE)")
    conn.commit(); conn.close()

init_db()

# --- DASHBOARD DE PERFORMANCE ---
def dashboard():
    st.title("📊 Painel de Performance (Custo/KM)")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    if not df_v.empty:
        for _, veic in df_v.iterrows():
            total_custo = df_os[df_os['placa'] == veic['placa']]['custo'].sum()
            custo_km = total_custo / veic['km_atual'] if veic['km_atual'] > 0 else 0
            
            with st.expander(f"🚛 {veic['placa']} - {veic['modelo']} | Condutor: {veic['motorista']}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("KM Atual", veic['km_atual'])
                c2.metric("Custo Total", f"R$ {total_custo:,.2f}")
                c3.metric("Eficiência (Custo/KM)", f"R$ {custo_km:.2f}")

# --- GESTÃO E APONTAMENTO ---
def gestao_frota():
    st.title("🚛 Gestão de Ativos")
    with st.form("form_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        motorista = st.text_input("Nome do Motorista")
        km = st.number_input("KM Atual", min_value=0)
        
        if st.form_submit_button("Registrar Veículo"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, motorista, km_atual) VALUES (?,?,?,?)", (placa, modelo, motorista, km))
            conn.commit(); conn.close(); st.success("Registrado!"); st.rerun()

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota"])
if menu == "Dashboard": dashboard()
else: gestao_frota()
