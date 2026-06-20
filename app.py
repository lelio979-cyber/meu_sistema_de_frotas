import streamlit as st
import sqlite3
import os

# Configuração da página e do banco
st.set_page_config(page_title="SGF-Pro V27", layout="wide")
conn = sqlite3.connect('frotas_v27.db', check_same_thread=False)

# Criar tabelas necessárias
conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")

# Inserir usuários padrão apenas uma vez
conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('user', '123', 'operador')")
conn.commit()
