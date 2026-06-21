import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Conexão
def get_conn():
    return sqlite3.connect("frota_elite.db", check_same_thread=False)

conn = get_conn()
conn.execute("""
    CREATE TABLE IF NOT EXISTS frota (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT, modelo TEXT, custo REAL, data_revisao TEXT, data_ipva TEXT
    )
""")

st.set_page_config(page_title="SGF-Fleet Pro", layout="wide")
st.title("🚛 Gestão de Frotas: Controle de Prazos")

tab1, tab2 = st.tabs(["➕ Cadastrar", "⚙️ Gerenciar (Editar/Excluir)"])

# 1. CADASTRO
with tab1:
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        custo = col3.number_input("Custo de Manutenção", min_value=0.0)
        col4, col5 = st.columns(2)
        data_revisao = col4.date_input("Próxima Revisão")
        data_ipva = col5.date_input("Vencimento IPVA")
        
        if st.form_submit_button("Salvar Veículo"):
            if placa:
                conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?,?,?,?,?)", 
                             (placa, modelo, custo, str(data_revisao), str(data_ipva)))
                conn.commit()
                st.success("Veículo salvo!")
            else:
                st.error("A placa é obrigatória.")

# 2. GERENCIAMENTO (EDIÇÃO E EXCLUSÃO)
with tab2:
    df = pd.read_sql("SELECT * FROM frota", conn)
    if not df.empty:
        # Seleção para ação
        veiculo_id = st.selectbox("Selecione o ID do veículo para editar/excluir", df['id'].tolist())
        
        # Obter dados atuais do veículo selecionado
        veiculo_selecionado = df[df['id'] == veiculo_id].iloc[0]
        
        with st.expander("Dados Atuais", expanded=True):
            st.write(f"**Placa:** {veiculo_selecionado['placa']} | **Modelo:** {veiculo_selecionado['modelo']}")
            
            # Botão de Excluir
            if st.button("🗑️ Excluir este veículo", type="primary"):
                conn.execute("DELETE FROM frota WHERE id = ?", (veiculo_id,))
                conn.commit()
                st.rerun()

            # Edição simples
            st.divider()
            novo_custo = st.number_input("Atualizar Custo", value=float(veiculo_selecionado['custo']))
            if st.button("Atualizar Custo"):
                conn.execute("UPDATE frota SET custo = ? WHERE id = ?", (novo_custo, veiculo_id))
                conn.commit()
                st.rerun()
    else:
        st.info("Nenhum veículo disponível para gerenciar.")

# 3. LISTAGEM GERAL
st.divider()
st.subheader("Veículos Ativos")
df_display = pd.read_sql("SELECT * FROM frota", conn)
st.dataframe(df_display, use_container_width=True)
