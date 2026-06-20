import streamlit as st
import pandas as pd
import os

FILE_NAME = "dados_frota.xlsx"

# --- BLOCO DE CRIAÇÃO AUTOMÁTICA ---
if not os.path.exists(FILE_NAME):
    # Cria o arquivo com as abas necessárias se ele não existir
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        pd.DataFrame(columns=['Placa', 'Modelo', 'Status']).to_excel(writer, sheet_name='Veiculos', index=False)
        pd.DataFrame(columns=['Placa', 'Servico', 'Custo', 'Data']).to_excel(writer, sheet_name='Manutencao', index=False)
    st.info("Arquivo Excel criado automaticamente!")

st.set_page_config(page_title="SGF Elite", layout="wide")
st.title("🚛 Gestão de Frotas (Excel Base)")

# Carrega os dados
df_veiculos = pd.read_excel(FILE_NAME, sheet_name="Veiculos")

# Interface
st.subheader("Cadastro de Veículos")
with st.form("form_veic", clear_on_submit=True):
    placa = st.text_input("Placa").upper()
    modelo = st.text_input("Modelo")
    if st.form_submit_button("Salvar"):
        novo = pd.DataFrame({'Placa': [placa], 'Modelo': [modelo], 'Status': ['Disponível']})
        df_atualizado = pd.concat([df_veiculos, novo], ignore_index=True)
        
        # Salva de volta no Excel
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl', mode='w') as writer:
            df_atualizado.to_excel(writer, sheet_name="Veiculos", index=False)
            pd.read_excel(FILE_NAME, sheet_name="Manutencao").to_excel(writer, sheet_name="Manutencao", index=False)
        
        st.success("Veículo cadastrado!")
        st.rerun()

st.dataframe(df_veiculos, use_container_width=True)
