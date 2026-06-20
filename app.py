import streamlit as st
import sqlite3
import pandas as pd

# MUDAMOS O NOME DO ARQUIVO PARA FORÇAR A CRIAÇÃO DE UM NOVO BANCO LIMPO
DB_NAME = "nova_frota_2026.db"

st.set_page_config(page_title="SGF-Fleet Pro", layout="wide")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Criamos todas as tabelas do zero
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, km_atual INTEGER, km_revisao INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, valor REAL, comprovante_link TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS abastecimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, litros REAL, km_percorrido REAL)")
    conn.commit()
    conn.close()

init_db()

# Navegação Simples
menu = st.sidebar.selectbox("Navegação", ["Dashboard", "Gestão de Ativos", "Multas", "Combustível"])

if menu == "Dashboard":
    st.title("📊 Painel")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    st.dataframe(df)

elif menu == "Gestão de Ativos":
    st.title("🚛 Cadastro")
    with st.form("c1"):
        p = st.text_input("Placa").upper()
        m = st.text_input("Modelo")
        mot = st.text_input("Motorista")
        k = st.number_input("KM Atual", 0)
        kr = st.number_input("KM Revisão", 0)
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?)", (p, m, mot, k, kr))
            conn.commit(); conn.close(); st.success("Salvo!"); st.rerun()

elif menu == "Multas":
    st.title("⚠️ Multas")
    with st.form("c2"):
        p = st.text_input("Placa").upper()
        v = st.number_input("Valor", 0.0)
        if st.form_submit_button("Registrar"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO multas (placa, valor) VALUES (?,?)", (p, v))
            conn.commit(); conn.close(); st.success("Salvo!"); st.rerun()

elif menu == "Combustível":
    st.title("⛽ Combustível")
    with st.form("c3"):
        p = st.text_input("Placa").upper()
        l = st.number_input("Litros", 0.1)
        if st.form_submit_button("Registrar"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO abastecimentos (placa, litros) VALUES (?,?)", (p, l))
            conn.commit(); conn.close(); st.success("Salvo!"); st.rerun()
