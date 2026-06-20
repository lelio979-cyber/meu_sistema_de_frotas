import streamlit as st
import sqlite3
import pandas as pd

# Nome do banco de dados (único e constante)
DB_NAME = "frota_base.db"

# 1. FUNÇÃO DE INICIALIZAÇÃO (Estrutura)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    conn.commit()
    conn.close()

# 2. INICIAR O PROJETO
init_db()

st.title("SGF-Fleet: Projeto do Zero")

# 3. INTERFACE BÁSICA
st.write("Sistema Iniciado com sucesso!")
