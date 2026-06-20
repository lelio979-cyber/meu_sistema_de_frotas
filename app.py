import streamlit as st
import sqlite3
import pandas as pd

# Conecta e cria a tabela simples (sem colunas de datas complexas por enquanto)
conn = sqlite3.connect("frota_elite.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, modelo TEXT, custo REAL)")
conn.commit()

st.title("🚛 Gestão de Frotas")

# Formulário simples
with st.form("form", clear_on_submit=True):
    placa = st.text_input("Placa")
    modelo = st.text_input("Modelo")
    custo = st.number_input("Custo")
    if st.form_submit_button("Salvar"):
        conn.execute("INSERT INTO frota (placa, modelo, custo) VALUES (?, ?, ?)", (placa, modelo, custo))
        conn.commit()
        st.rerun()

# Exibição
st.subheader("Veículos")
df = pd.read_sql("SELECT * FROM frota", conn)
st.dataframe(df)
