import streamlit as st
import sqlite3
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Gestão de Frota Pro", layout="wide")

# 1. FUNÇÃO DE CONEXÃO SEGURA
def get_db():
    conn = sqlite3.connect("frota.db")
    return conn

# 2. CRIAÇÃO DAS TABELAS (Apenas uma vez)
def setup():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km INTEGER)")
    conn.commit()
    conn.close()

setup()

# 3. INTERFACE
st.title("🚛 Gestão de Frota")

menu = st.sidebar.radio("Menu", ["Cadastro", "Dashboard"])

if menu == "Cadastro":
    st.subheader("Novo Veículo")
    with st.form("form_cad"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Inicial", 0)
        submit = st.form_submit_button("Salvar")
        
        if submit:
            conn = get_db()
            try:
                conn.execute("INSERT INTO veiculos VALUES (?, ?, ?)", (placa, modelo, km))
                conn.commit()
                st.success("Veículo salvo!")
            except sqlite3.IntegrityError:
                st.error("Placa já existe!")
            conn.close()

elif menu == "Dashboard":
    st.subheader("Frota")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    st.dataframe(df)
