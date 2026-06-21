import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Nome do banco alterado para evitar conflitos com arquivos corrompidos
DB_NAME = "frota_nova.db"

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS frota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT,
            modelo TEXT,
            custo REAL,
            data_revisao TEXT,
            data_ipva TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

st.title("🚛 Gestão de Frotas")

# Formulário
with st.form("cadastro", clear_on_submit=True):
    placa = st.text_input("Placa").upper()
    modelo = st.text_input("Modelo")
    custo = st.number_input("Custo", min_value=0.0)
    data_revisao = st.date_input("Data Revisão")
    data_ipva = st.date_input("Data IPVA")
    
   if st.form_submit_button("Salvar Veículo"):
    if not placa:
        st.error("A placa é obrigatória!")
    else:
        conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?,?,?,?,?)", 
                     (placa, modelo, custo, str(data_revisao), str(data_ipva)))
        conn.commit()
        st.success("Salvo!")
        st.rerun()

# Listagem
st.subheader("Veículos")
df = pd.read_sql("SELECT * FROM frota", conn)

if not df.empty:
    hoje = datetime.now().strftime('%Y-%m-%d')
    df['Status Rev'] = df['data_revisao'].apply(lambda x: "⚠️" if x < hoje else "✅")
    st.dataframe(df, use_container_width=True)
else:
    st.write("Nenhum dado ainda.")
