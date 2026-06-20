import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Gestão de Frota Pro", layout="wide")

def get_db():
    conn = sqlite3.connect("frota.db")
    return conn

def setup():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL)")
    # Nova tabela de combustíveis
    conn.execute("CREATE TABLE IF NOT EXISTS combustivel (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, litros REAL, km_rodado REAL)")
    conn.commit()
    conn.close()

setup()

st.title("🚛 Gestão de Frota")
menu = st.sidebar.radio("Menu", ["Cadastro", "Manutenção", "Combustível", "Dashboard"])

# [Mantenha os módulos anteriores de Cadastro e Manutenção aqui]
# --- NOVO MÓDULO ---
if menu == "Combustível":
    st.subheader("Registrar Abastecimento")
    conn = get_db()
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not veiculos.empty:
        with st.form("form_comb"):
            placa = st.selectbox("Veículo", veiculos['placa'])
            litros = st.number_input("Litros Abastecidos", 0.1)
            km_rodado = st.number_input("KM Rodado desde último abastecimento", 0.1)
            if st.form_submit_button("Salvar Combustível"):
                conn = get_db()
                conn.execute("INSERT INTO combustivel (placa, litros, km_rodado) VALUES (?, ?, ?)", (placa, litros, km_rodado))
                conn.commit()
                conn.close()
                media = km_rodado / litros
                st.success(f"Média calculada: {media:.2f} KM/L!")
    else: st.warning("Cadastre um veículo primeiro.")

elif menu == "Dashboard":
    st.subheader("Painel Geral")
    conn = get_db()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_comb = pd.read_sql("SELECT * FROM combustivel", conn)
    conn.close()
    st.write("### Consumo de Combustível")
    st.dataframe(df_comb)
