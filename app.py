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

# --- ÁREA LOGADA ---
st.sidebar.title(f"Perfil: {st.session_state['perfil']}")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

# Definindo o menu baseado no perfil
menu_opcoes = ["Dashboard"]
if st.session_state['perfil'] == 'admin':
    menu_opcoes.append("Cadastro de Veículos")

menu = st.sidebar.radio("Navegação", menu_opcoes)

# --- FUNÇÃO DE CADASTRO ---
def modulo_cadastro():
    st.subheader("Cadastro de Veículos (Admin)")
    with st.form("form_veiculo"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?, ?)", (placa, modelo))
            conn.commit()
            st.success(f"Veículo {placa} salvo!")

# --- LÓGICA DE EXIBIÇÃO DO MENU ---
if menu == "Dashboard":
    st.title("Bem-vindo ao SGF-Pro")
    st.write(f"Logado como: {st.session_state['perfil']}")
elif menu == "Cadastro de Veículos":
    modulo_cadastro()
