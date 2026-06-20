import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SGF-Fleet Rápido", layout="centered")

def get_db(): return sqlite3.connect("frota.db")

# Inserção rápida de dados
st.title("🚛 Entrada Rápida de Dados")

tab1, tab2, tab3 = st.tabs(["Veículos", "Manutenção", "Combustível"])

with tab1:
    with st.form("c1"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar Veículo"):
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?, ?)", (placa, modelo))
            conn.commit()
            st.success("Salvo!")

with tab2:
    with st.form("c2"):
        placa_os = st.selectbox("Placa", pd.read_sql("SELECT placa FROM veiculos", get_db())['placa'])
        servico = st.text_input("Serviço")
        if st.form_submit_button("Salvar OS"):
            conn = get_db()
            conn.execute("INSERT INTO os (placa, servico) VALUES (?, ?)", (placa_os, servico))
            conn.commit()
            st.success("OS salva!")

with tab3:
    st.dataframe(pd.read_sql("SELECT * FROM veiculos", get_db()))
    st.dataframe(pd.read_sql("SELECT * FROM os", get_db()))
