import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "frota_base.db"

# 1. Inicializa o banco de dados
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Criamos a tabela mínima necessária
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    conn.commit()
    conn.close()

init_db()

st.title("SGF-Fleet: Módulo de Cadastro")

# 2. Formulário para adicionar veículos
with st.form("form_cadastro"):
    placa = st.text_input("Placa do Veículo (Ex: ABC-1234)").upper()
    modelo = st.text_input("Modelo do Veículo")
    btn_salvar = st.form_submit_button("Salvar Veículo")

    if btn_salvar:
        if placa and modelo:
            conn = sqlite3.connect(DB_NAME)
            try:
                conn.execute("INSERT INTO veiculos (placa, modelo) VALUES (?, ?)", (placa, modelo))
                conn.commit()
                st.success(f"Veículo {placa} salvo com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Erro: Esta placa já existe no sistema.")
            finally:
                conn.close()
        else:
            st.warning("Por favor, preencha todos os campos.")

# 3. Exibição da lista de veículos
st.divider()
st.subheader("Veículos Cadastrados")
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM veiculos", conn)
conn.close()

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nenhum veículo cadastrado.")
