import streamlit as st
import pandas as pd
import os

FILE_NAME = "dados_frota.xlsx"

# Verifica se o arquivo existe
if not os.path.exists(FILE_NAME):
    st.error(f"O arquivo {FILE_NAME} não foi encontrado na pasta! Por favor, crie-o manualmente com as abas 'Veiculos' e 'Manutencao'.")
    st.stop()

st.set_page_config(page_title="SGF Excel Pro", layout="wide")
st.title("🚛 SGF-Fleet Pro")

menu = st.sidebar.radio("Navegação", ["Frota", "Manutenção"])

# Carregamento seguro
try:
    df_veiculos = pd.read_excel(FILE_NAME, sheet_name="Veiculos")
    df_manut = pd.read_excel(FILE_NAME, sheet_name="Manutencao")
except Exception as e:
    st.error(f"Erro ao ler o Excel: {e}")
    st.stop()

if menu == "Frota":
    st.header("Gestão de Veículos")
    with st.form("cad_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Cadastrar"):
            novo_dado = pd.DataFrame({'Placa': [placa], 'Modelo': [modelo], 'Status': ['Disponível']})
            df_novo = pd.concat([df_veiculos, novo_dado], ignore_index=True)
            
            with pd.ExcelWriter(FILE_NAME, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_novo.to_excel(writer, sheet_name="Veiculos", index=False)
            st.success("Salvo!")
            st.rerun()
    st.dataframe(df_veiculos, use_container_width=True)
