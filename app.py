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
    st.title("📝 Gestão de Veículos")
    
    # Formulário de Cadastro
    with st.form("cad_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        submit = st.form_submit_button("Salvar Veículo")
        
        if submit:
            if placa:
                # O comando INSERT OR REPLACE evita duplicidade usando a Placa como chave
                conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
                conn.commit()
                st.success(f"Veículo {placa} salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, informe a placa.")
# Exibir dados
st.sidebar.divider()
st.sidebar.write("Dados da Frota:")
df = pd.read_sql("SELECT * FROM veiculos", conn)
st.sidebar.dataframe(df)
