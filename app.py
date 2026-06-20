import streamlit as st
import pandas as pd
import os

# Nome do arquivo de banco de dados
FILE_NAME = "dados_frota.xlsx"

# --- FUNÇÃO DE INICIALIZAÇÃO ---
def init_db():
    if not os.path.exists(FILE_NAME):
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
            pd.DataFrame(columns=['Placa', 'Modelo', 'Motorista', 'Custo']).to_excel(writer, sheet_name='Frota', index=False)
        st.success("Banco de dados Excel criado com sucesso!")

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="SGF Excel Pro", layout="wide")
init_db()

st.title("🚛 SGF-Fleet Pro (Base Excel)")

# --- LÓGICA DE DADOS ---
def carregar_dados():
    return pd.read_excel(FILE_NAME, sheet_name='Frota')

def salvar_dados(df):
    df.to_excel(FILE_NAME, sheet_name='Frota', index=False)

# --- NAVEGAÇÃO E INPUTS ---
aba1, aba2 = st.tabs(["Cadastro", "Dashboard"])

with aba1:
    with st.form("cad_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        motorista = col1.text_input("Nome do Motorista")
        custo = col2.number_input("Custo de Manutenção (R$)", min_value=0.0)
        
        if st.form_submit_button("Salvar Veículo"):
            df = carregar_dados()
            novo_dado = pd.DataFrame({'Placa': [placa], 'Modelo': [modelo], 'Motorista': [motorista], 'Custo': [custo]})
            df = pd.concat([df, novo_dado], ignore_index=True)
            salvar_dados(df)
            st.success(f"Veículo {placa} salvo no Excel!")
            st.rerun()

with aba2:
    st.subheader("Frota Ativa")
    df = carregar_dados()
    st.dataframe(df, use_container_width=True)
    
    if not df.empty:
        st.metric("Custo Total da Frota", f"R$ {df['Custo'].sum():,.2f}")
