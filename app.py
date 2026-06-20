import streamlit as st
import sqlite3
import pandas as pd

# Conecta ao banco
conn = sqlite3.connect("frota_elite.db", check_same_thread=False)

# Adiciona as colunas com segurança (IF NOT EXISTS)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE frota ADD COLUMN data_revisao TEXT")
    cursor.execute("ALTER TABLE frota ADD COLUMN data_ipva TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass # Colunas já existem, tudo bem!

st.title("🚛 Gestão de Frotas: Controle de Prazos")

# Formulário atualizado
with st.form("form", clear_on_submit=True):
    placa = st.text_input("Placa").upper()
    modelo = st.text_input("Modelo")
    custo = st.number_input("Custo", min_value=0.0)
    data_revisao = st.date_input("Próxima Revisão")
    data_ipva = st.date_input("Vencimento IPVA")
    
    if st.form_submit_button("Salvar"):
        conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?, ?, ?, ?, ?)", 
                     (placa, modelo, custo, str(data_revisao), str(data_ipva)))
        conn.commit()
        st.rerun()

# Exibição
st.subheader("Veículos Ativos")
df = pd.read_sql("SELECT * FROM frota", conn)
st.dataframe(df, use_container_width=True)
