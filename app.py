import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SGF Elite", layout="wide")

# Conexão
conn = sqlite3.connect("sgf_base.db", check_same_thread=False)

# Garantir estrutura limpa
conn.execute("DROP TABLE IF EXISTS veiculos")
conn.execute("CREATE TABLE veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
conn.commit()

# Sidebar apenas para menu
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Cadastro Veículos"])

if menu == "Dashboard":
    st.title("Painel SGF")
    st.write("Sistema rodando. Use o menu lateral para cadastrar.")

elif menu == "Cadastro Veículos":
    st.title("📝 Gestão de Veículos")
    
    # Formulário
    with st.form("cad_form", clear_on_submit=True):
        placa = st.text_input("Placa (Ex: AAA1111)").upper()
        modelo = st.text_input("Modelo")
        submit = st.form_submit_button("Salvar")
        
        if submit:
            if placa:
                try:
                    conn.execute("INSERT INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
                    conn.commit()
                    st.success("Veículo cadastrado!")
                except sqlite3.IntegrityError:
                    st.error("Erro: Esta placa já está cadastrada.")
            else:
                st.warning("Campo placa é obrigatório.")

    # Tabela na área central
    st.divider()
    st.subheader("Frota Ativa")
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    st.dataframe(df, use_container_width=True)
