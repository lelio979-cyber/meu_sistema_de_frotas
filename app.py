import streamlit as st

st.title("FleetX - Teste de Funcionamento")
st.write("Se consegue ler esta mensagem, o sistema está vivo e o ambiente está a funcionar corretamente!")

⚙️_opcao = st.sidebar.radio("Menu de Teste:", ["Início", "Sobre"])
if ⚙️_opcao == "Início":
    st.success("Tudo pronto para avançar!")
else:
    st.info("O ambiente está estável.")
