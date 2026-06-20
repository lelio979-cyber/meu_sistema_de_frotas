import streamlit as st
import sqlite3
import pandas as pd

# --- BANCO DE DADOS ---
conn = sqlite3.connect("sgf_frota.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, modelo TEXT, custo REAL, motorista TEXT)")
conn.commit()

st.set_page_config(layout="wide", page_title="SGF-Fleet Elite")
st.title("🚛 SGF-Fleet Elite: Gestão Completa")

aba1, aba2, aba3 = st.tabs(["Frota e Motoristas", "Financeiro e Alertas", "Dados"])

# --- 1. GESTÃO DE FROTA E MOTORISTAS ---
with aba1:
    with st.form("cad_frota"):
        c1, c2, c3 = st.columns(3)
        placa = c1.text_input("Placa").upper()
        modelo = c2.text_input("Modelo")
        motorista = c3.text_input("Nome do Motorista")
        custo = st.number_input("Custo de Manutenção (R$)", min_value=0.0)
        
        if st.form_submit_button("Registrar Veículo"):
            conn.execute("INSERT INTO frota (placa, modelo, custo, motorista) VALUES (?,?,?,?)", (placa, modelo, custo, motorista))
            conn.commit()
            st.rerun()

# --- 2. RELATÓRIOS E ALERTAS FINANCEIROS ---
with aba2:
    df = pd.read_sql("SELECT * FROM frota", conn)
    if not df.empty:
        st.subheader("Análise de Custos")
        # Alerta: Se o custo passar de R$ 500, o sistema destaca
        for _, row in df.iterrows():
            if row['custo'] > 500:
                st.error(f"⚠️ ALERTA: Veículo {row['placa']} está com custo elevado (R$ {row['custo']:.2f})!")
            else:
                st.success(f"✅ Veículo {row['placa']} dentro dos limites.")
    else:
        st.info("Nenhum registro encontrado.")

# --- 3. DADOS (VISUALIZAÇÃO) ---
with aba3:
    st.subheader("Gestão de Dados")
    df = pd.read_sql("SELECT * FROM frota", conn)
    st.dataframe(df, use_container_width=True)
    
    if st.button("Limpar Base de Dados"):
        conn.execute("DELETE FROM frota")
        conn.commit()
        st.rerun()
