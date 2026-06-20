import streamlit as st
import sqlite3
import pandas as pd

# Configuração da página
st.set_page_config(page_title="SGF-Pro Base", layout="wide")

# Conexão com o banco de dados
def get_db():
    conn = sqlite3.connect('frotas_limpo.db', check_same_thread=False)
    return conn

# Inicialização de tabelas (Força a criação na primeira vez)
def init_tables():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY, 
            modelo TEXT
        )
    """)
    conn.commit()
    conn.close()

# Executa a inicialização
init_tables()

# Interface Principal
def main():
    st.title("SGF-Pro V22 - Base Estável")
    st.write("Sistema rodando com sucesso!")
    
    # Menu de navegação simples
    menu = st.sidebar.radio("Navegação", ["Dashboard"])
    
    if menu == "Dashboard":
        st.success("O sistema base está operacional.")

if __name__ == "__main__":
    main()
