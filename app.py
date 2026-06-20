import streamlit as st
import pandas as pd

# Define a estrutura dos dados
if 'frota' not in st.session_state:
    st.session_state.frota = pd.DataFrame(columns=['Placa', 'Modelo'])

st.title("🚛 Gestão de Frotas (Versão Sem Erros)")

# Formulário
with st.form("cad_form"):
    placa = st.text_input("Placa")
    modelo = st.text_input("Modelo")
    if st.form_submit_button("Salvar"):
        novo_veiculo = pd.DataFrame({'Placa': [placa], 'Modelo': [modelo]})
        st.session_state.frota = pd.concat([st.session_state.frota, novo_veiculo], ignore_index=True)
        st.success("Veículo cadastrado!")

# Exibe a tabela
st.subheader("Frota Ativa")
st.table(st.session_state.frota)
