import streamlit as st
import sqlite3
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="SGF Elite", layout="wide")

# Conexão com Banco de Dados (Cria se não existir)
conn = sqlite3.connect("sgf_base.db", check_same_thread=False)

def init_db():
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    conn.commit()

init_db()

# Navegação
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Cadastro Veículos"])

if menu == "Dashboard":
    st.title("Bem-vindo ao SGF Elite")
    st.write("Sistema operacional e banco de dados conectado.")
    
elif menu == "Cadastro Veículos":
    st.title("Cadastro de Veículos")
    with st.form("cad_form"):
        placa = st.text_input("Placa")
        modelo = st.text_input("Modelo")
        submit = st.form_submit_button("Salvar")
        if submit:
            try:
                conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
                conn.commit()
                st.success("Veículo salvo!")
                st.rerun() # <--- ISSO força o sistema a recarregar e mostrar o novo dado na tabela
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
# Exibir dados
st.sidebar.divider()
st.sidebar.write("Dados da Frota:")
df = pd.read_sql("SELECT * FROM veiculos", conn)
st.sidebar.dataframe(df)
