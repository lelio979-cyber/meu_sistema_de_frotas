import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO ---
def init_db():
    conn = sqlite3.connect("frota_elite.db", check_same_thread=False)
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

st.set_page_config(page_title="SGF-Fleet Pro", layout="wide")
st.title("🚛 Gestão de Frotas: Controle de Prazos")

# --- FORMULÁRIO DE CADASTRO ---
with st.form("form_cadastro", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    placa = col1.text_input("Placa").upper()
    modelo = col2.text_input("Modelo")
    custo = col3.number_input("Custo de Manutenção", min_value=0.0)
    
    col4, col5 = st.columns(2)
    data_revisao = col4.date_input("Próxima Revisão")
    data_ipva = col5.date_input("Vencimento IPVA")
    
    if st.form_submit_button("Salvar Veículo"):
        conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?, ?, ?, ?, ?)", 
                     (placa, modelo, custo, str(data_revisao), str(data_ipva)))
        conn.commit()
        st.success("Veículo salvo!")
        st.rerun()

# --- LISTAGEM E ALERTAS ---
st.subheader("Veículos Ativos")
df = pd.read_sql("SELECT * FROM frota", conn)

if not df.empty:
    # Lógica de Alerta
    hoje = datetime.now().strftime('%Y-%m-%d')
    
    # Criar colunas de status
    df['Status Rev'] = df['data_revisao'].apply(lambda x: "⚠️ ATRAZADO" if x < hoje else "✅ EM DIA")
    df['Status IPVA'] = df['data_ipva'].apply(lambda x: "⚠️ ATRAZADO" if x < hoje else "✅ EM DIA")

    # Filtro de Alertas
    if st.checkbox("🔍 Filtrar apenas veículos com pendências"):
        df_alertas = df[(df['Status Rev'] == "⚠️ ATRAZADO") | (df['Status IPVA'] == "⚠️ ATRAZADO")]
        st.warning("Veículos que precisam de atenção:")
        st.dataframe(df_alertas, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
        
    # Botão de Excluir (simples)
    if st.button("Limpar todos os dados"):
        conn.execute("DELETE FROM frota")
        conn.commit()
        st.rerun()
else:
    st.info("Nenhum veículo cadastrado.")
