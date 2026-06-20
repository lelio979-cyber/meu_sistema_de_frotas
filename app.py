import streamlit as st
import sqlite3

try:
    st.set_page_config(page_title="Teste de Diagnóstico", layout="wide")
    st.title("Teste de Execução")
    
    conn = sqlite3.connect('teste.db')
    st.success("Conexão com SQLite realizada com sucesso!")
    
    st.write("Se você está vendo esta mensagem, o Python e o Streamlit estão rodando perfeitamente.")
    
except Exception as e:
    st.error(f"Erro detectado: {e}")
