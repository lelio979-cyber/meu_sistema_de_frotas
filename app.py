import streamlit as st
import sqlite3
import pandas as pd

# Configuração Base
st.set_page_config(page_title="SGF-Pro V21", layout="wide")

# Função de Banco de Dados (Segura e Recriável)
def init_db():
    conn = sqlite3.connect('frotas_v21.db', check_same_thread=False)
    # Criamos a tabela mínima para o sistema rodar
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    conn.commit()
    return conn

conn = init_db()

# Navegação Principal (Onde vamos "pendurar" as futuras abas)
def main():
    st.sidebar.title("Navegação SGF-Pro")
    menu = st.sidebar.radio("Módulos", ["Dashboard", "Veículos"])
    
    if menu == "Dashboard":
        st.header("Bem-vindo ao SGF-Pro V21")
        st.info("O sistema base está estável e pronto para expansão.")
    elif menu == "Veículos":
        st.header("Módulo de Veículos")
        # Implementaremos o formulário aqui no próximo passo
        st.write("Aguardando definição de campos.")

if __name__ == "__main__":
    main()
