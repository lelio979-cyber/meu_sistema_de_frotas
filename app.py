import streamlit as st

st.title("FleetX - Teste de Funcionamento")
st.write("Se você está lendo isso, o sistema está vivo e o ambiente está funcionando!")

opcao = st.sidebar.radio("Menu de Teste:", ["Início", "Sobre"])
if opcao == "Início":
    st.success("Tudo pronto para avançar!")
else:
    st.info("O ambiente está estável.")
