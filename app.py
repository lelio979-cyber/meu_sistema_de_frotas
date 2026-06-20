import streamlit as st
import pandas as pd
import banco # Importa a lógica do banco que criamos acima

# Inicializa o banco ao abrir o app
banco.init_db()

def main():
    st.title("Sistema de Gestão de Frota")
    
    # Aqui você coloca as funções (Cadastro, Edição, etc)
    # Exemplo simples para testar:
    if st.button("Verificar Banco"):
        st.write("Banco de dados pronto para uso!")

if __name__ == "__main__":
    main()
