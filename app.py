import streamlit as st
import sqlite3
import pandas as pd

# 1. FUNÇÕES DE BANCO DE DADOS
def get_db():
    return sqlite3.connect("frota.db")

def registrar_log(acao, tabela):
    conn = get_db()
    conn.execute("INSERT INTO logs (acao, tabela) VALUES (?, ?)", (acao, tabela))
    conn.commit()
    conn.close()

def setup_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS checklist (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, acao TEXT, tabela TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

setup_db()

# 2. INTERFACE
st.title("🚛 SGF-Fleet Enterprise")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro", "Checklist"])

if menu == "Dashboard":
    st.subheader("Painel Geral")
    conn = get_db()
    df_logs = pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", conn)
    conn.close()
    st.write("### Auditoria Recente")
    st.dataframe(df_logs)

elif menu == "Cadastro":
    with st.form("c1"):
        placa = st.text_input("Placa")
        if st.form_submit_button("Salvar"):
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO veiculos (placa) VALUES (?)", (placa,))
            conn.commit()
            conn.close()
            registrar_log(f"Cadastro de {placa}", "veiculos")
            st.success("Salvo!")

elif menu == "Checklist":
    with st.form("c2"):
        placa = st.text_input("Placa do veículo")
        status = st.selectbox("Status", ["OK", "Necessita Reparo"])
        if st.form_submit_button("Registrar"):
            conn = get_db()
            conn.execute("INSERT INTO checklist (placa, status) VALUES (?, ?)", (placa, status))
            conn.commit()
            conn.close()
            registrar_log(f"Checklist {placa} - {status}", "checklist")
            st.success("Checklist salvo!")
