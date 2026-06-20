import streamlit as st

# Configuração da página
st.set_page_config(page_title="Sistema Seguro", layout="centered")

st.title("🚛 Gestão de Frota (Modo Seguro)")

# Usamos o 'session_state' do Streamlit para guardar os dados na memória do navegador
if 'frota' not in st.session_state:
    st.session_state.frota = []

# Formulário
with st.form("form_seguro"):
    placa = st.text_input("Placa do Veículo")
    modelo = st.text_input("Modelo")
    if st.form_submit_button("Cadastrar"):
        st.session_state.frota.append({"Placa": placa, "Modelo": modelo})
        st.success("Veículo cadastrado!")

# Tabela
st.write("### Frota Cadastrada:")
if st.session_state.frota:
    import pandas as pd
    st.table(pd.DataFrame(st.session_state.frota))
else:
    st.info("Nenhum veículo cadastrado.")
