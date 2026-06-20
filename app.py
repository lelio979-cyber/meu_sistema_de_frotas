import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Gestão de Frota Pro", layout="wide")

def get_db():
    conn = sqlite3.connect("frota.db")
    return conn

def setup():
    conn = get_db()
    # Tabela de Veículos
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km INTEGER)")
    # Tabela de Manutenção (OS) - Nova tabela
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL)")
    conn.commit()
    conn.close()

setup()

st.title("🚛 Gestão de Frota")
menu = st.sidebar.radio("Menu", ["Cadastro", "Manutenção", "Dashboard"])

if menu == "Cadastro":
    st.subheader("Novo Veículo")
    with st.form("form_cad"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Inicial", 0)
        if st.form_submit_button("Salvar"):
            conn = get_db()
            try:
                conn.execute("INSERT INTO veiculos VALUES (?, ?, ?)", (placa, modelo, km))
                conn.commit()
                st.success("Veículo salvo!")
            except: st.error("Erro ao salvar.")
            conn.close()

elif menu == "Manutenção":
    st.subheader("Registrar Manutenção")
    conn = get_db()
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not veiculos.empty:
        with st.form("form_os"):
            placa = st.selectbox("Veículo", veiculos['placa'])
            servico = st.text_input("Serviço Realizado")
            custo = st.number_input("Custo (R$)", 0.0)
            if st.form_submit_button("Salvar OS"):
                conn = get_db()
                conn.execute("INSERT INTO os (placa, servico, custo) VALUES (?, ?, ?)", (placa, servico, custo))
                conn.commit()
                conn.close()
                st.success("OS registrada!")
    else: st.warning("Cadastre um veículo antes.")

elif menu == "Dashboard":
    st.subheader("Painel Geral")
    conn = get_db()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    st.write("### Veículos")
    st.dataframe(df_v)
    st.write("### Manutenções")
    st.dataframe(df_os)
