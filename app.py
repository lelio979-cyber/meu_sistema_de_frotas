import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# 1. REMOÇÃO DE BANCO ANTIGO (Caso exista conflito)
# Se você quiser manter os dados, não execute esta parte. 
# Se o erro persistir, descomente a linha abaixo para forçar a recriação:
# if os.path.exists("frota_elite.db"): os.remove("frota_elite.db")

# 2. CONEXÃO E ESTRUTURA
def get_conn():
    return sqlite3.connect("frota_elite.db", check_same_thread=False)

conn = get_conn()
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

st.set_page_config(page_title="SGF-Fleet Pro", layout="wide")
st.title("🚛 Gestão de Frotas: Controle de Prazos")

# 3. FORMULÁRIO
with st.form("form_cadastro", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    placa = col1.text_input("Placa").upper()
    modelo = col2.text_input("Modelo")
    custo = col3.number_input("Custo de Manutenção", min_value=0.0)
    
    col4, col5 = st.columns(2)
    data_revisao = col4.date_input("Próxima Revisão")
    data_ipva = col5.date_input("Vencimento IPVA")
    
    if st.form_submit_button("Salvar Veículo"):
        conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?,?,?,?,?)", 
                     (placa, modelo, custo, str(data_revisao), str(data_ipva)))
        conn.commit()
        st.success("Veículo salvo!")
        st.rerun()

# 4. LISTAGEM
st.subheader("Veículos Ativos")
df = pd.read_sql("SELECT * FROM frota", conn)

if not df.empty:
    hoje = datetime.now().strftime('%Y-%m-%d')
    
    # Criar colunas de status
    df['Status Rev'] = df['data_revisao'].apply(lambda x: "⚠️ ATRAZADO" if x < hoje else "✅ EM DIA")
    df['Status IPVA'] = df['data_ipva'].apply(lambda x: "⚠️ ATRAZADO" if x < hoje else "✅ EM DIA")

    st.dataframe(df, use_container_width=True)
else:
    st.info("Nenhum veículo cadastrado.")
