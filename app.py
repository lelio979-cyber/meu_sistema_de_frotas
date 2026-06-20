import streamlit as st
import sqlite3
import pandas as pd

# --- CONEXÃO E CONFIGURAÇÃO ---
def get_db():
    conn = sqlite3.connect("sgf_frota.db", check_same_thread=False)
    return conn

# Inicializa o banco de dados e garante a estrutura correta
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS frota (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            placa TEXT, 
            modelo TEXT, 
            custo REAL, 
            motorista TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

st.set_page_config(layout="wide", page_title="SGF-Fleet Elite")
st.title("🚛 SGF-Fleet Elite: Gestão Completa")

# --- INTERFACE ---
aba1, aba2 = st.tabs(["Cadastro", "Dashboard e Alertas"])

with aba1:
    with st.form("cad_frota", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        placa = c1.text_input("Placa").upper()
        modelo = c2.text_input("Modelo")
        motorista = c3.text_input("Nome do Motorista")
        custo = st.number_input("Custo de Manutenção (R$)", min_value=0.0)
        
        if st.form_submit_button("Registrar Veículo"):
            conn = get_db()
            conn.execute("INSERT INTO frota (placa, modelo, custo, motorista) VALUES (?,?,?,?)", 
                         (placa, modelo, custo, motorista))
            conn.commit()
            conn.close()
            st.success("Veículo registrado!")
            st.rerun()

with aba2:
    conn = get_db()
    df = pd.read_sql("SELECT * FROM frota", conn)
    conn.close()
    
    if not df.empty:
        st.subheader("Análise de Custos")
        st.dataframe(df, use_container_width=True)
        
        # Alertas Financeiros
        for _, row in df.iterrows():
            if row['custo'] > 500:
                st.error(f"⚠️ ALERTA: Veículo {row['placa']} (Motorista: {row['motorista']}) ultrapassou o limite com R$ {row['custo']:.2f}!")
    else:
        st.info("Nenhum veículo cadastrado ainda.")
