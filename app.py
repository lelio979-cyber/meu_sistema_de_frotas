import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Gestão de Frota Pro", layout="wide")

def get_db():
    conn = sqlite3.connect("frota.db")
    return conn

def setup():
    conn = get_db()
    # Tabelas já existentes
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS combustivel (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, litros REAL, km_rodado REAL)")
    # Nova Tabela de Multas
    conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, valor REAL, comprovante TEXT)")
    conn.commit()
    conn.close()

setup()

st.title("🚛 Gestão de Frota")
menu = st.sidebar.radio("Menu", ["Cadastro", "Manutenção", "Combustível", "Multas", "Dashboard"])

# [Inclua aqui a lógica anterior de Cadastro, Manutenção e Combustível]

if menu == "Multas":
    st.subheader("Registrar Multa")
    conn = get_db()
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not veiculos.empty:
        with st.form("form_multa"):
            placa = st.selectbox("Veículo", veiculos['placa'])
            valor = st.number_input("Valor da Multa (R$)", 0.0)
            foto = st.text_input("Link da Foto/Comprovante")
            if st.form_submit_button("Salvar Multa"):
                conn = get_db()
                conn.execute("INSERT INTO multas (placa, valor, comprovante) VALUES (?, ?, ?)", (placa, valor, foto))
                conn.commit()
                conn.close()
                st.success("Multa registrada!")
    else: st.warning("Cadastre um veículo antes.")

elif menu == "Dashboard":
    st.subheader("Painel Geral")
    conn = get_db()
    df_multas = pd.read_sql("SELECT * FROM multas", conn)
    conn.close()
    st.write("### Histórico de Multas")
    st.dataframe(df_multas)
