import streamlit as st
import pandas as pd
import os

# Configuração
FILE_NAME = "dados_frota.xlsx"

def carregar_dados(aba):
    if not os.path.exists(FILE_NAME):
        return pd.DataFrame()
    return pd.read_excel(FILE_NAME, sheet_name=aba)

def salvar_dados(df, aba):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=aba, index=False)

st.set_page_config(page_title="SGF Excel Pro", layout="wide")
st.title("🚛 SGF-Fleet Pro (Versão Excel)")

menu = st.sidebar.radio("Navegação", ["Frota", "Manutenção"])

if menu == "Frota":
    st.header("Gestão de Veículos")
    df = carregar_dados("Veiculos")
    
    with st.form("cad_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Cadastrar"):
            novo_dado = pd.DataFrame({'Placa': [placa], 'Modelo': [modelo], 'Status': ['Disponível']})
            df = pd.concat([df, novo_dado], ignore_index=True)
            salvar_dados(df, "Veiculos")
            st.success("Veículo salvo!")
            st.rerun()
    
    st.dataframe(df, use_container_width=True)

elif menu == "Manutenção":
    st.header("Registro de OS")
    df_m = carregar_dados("Manutencao")
    
    with st.form("os_form"):
        placa = st.text_input("Placa do Veículo")
        servico = st.text_input("Serviço")
        custo = st.number_input("Custo R$")
        if st.form_submit_button("Lançar OS"):
            novo_os = pd.DataFrame({'Placa': [placa], 'Servico': [servico], 'Custo': [custo], 'Data': [pd.Timestamp.now()]})
            df_m = pd.concat([df_m, novo_os], ignore_index=True)
            salvar_dados(df_m, "Manutencao")
            st.success("OS Lançada!")
            st.rerun()

    st.dataframe(df_m, use_container_width=True)
