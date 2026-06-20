import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SGF-Fleet Elite Pro", layout="wide")
DB_NAME = "sgf_fleet_elite.db"

# --- INICIALIZAÇÃO COM NOVAS TABELAS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Tabela Multas
    conn.execute("""CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, 
        valor REAL, data DATE, comprovante_link TEXT)""")
    # Tabela Combustível
    conn.execute("""CREATE TABLE IF NOT EXISTS abastecimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, 
        litros REAL, km_percorrido REAL)""")
    conn.commit(); conn.close()

init_db()

# --- MÓDULO DE MULTAS ---
def gestao_multas():
    st.title("⚠️ Registro de Multas")
    with st.form("form_multa"):
        placa = st.text_input("Placa do Veículo").upper()
        motorista = st.text_input("Motorista Responsável")
        valor = st.number_input("Valor da Multa (R$)", min_value=0.0)
        link = st.text_input("Link ou Caminho da Foto/Comprovante")
        if st.form_submit_button("Registrar Multa"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO multas (placa, motorista, valor, comprovante_link) VALUES (?,?,?,?)", 
                         (placa, motorista, valor, link))
            conn.commit(); conn.close(); st.success("Multa registrada!")

# --- MÓDULO DE COMBUSTÍVEL ---
def controle_combustivel():
    st.title("⛽ Controle de Consumo (KM/L)")
    with st.form("form_combustivel"):
        placa = st.text_input("Placa do Veículo").upper()
        litros = st.number_input("Litros Abastecidos", min_value=0.1)
        km_rodado = st.number_input("KM Percorrido desde último abastecimento", min_value=0.1)
        if st.form_submit_button("Calcular Média"):
            media = km_rodado / litros
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO abastecimentos (placa, litros, km_percorrido) VALUES (?,?,?)", 
                         (placa, litros, km_rodado))
            conn.commit(); conn.close()
            st.success(f"Média calculada: {media:.2f} KM/L. Dados salvos!")

# --- MENU DE NAVEGAÇÃO ---
st.sidebar.title("SGF-Fleet Elite")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Ativos", "Lançar OS", "Apontar KM", "Multas", "Combustível", "Relatório"])

if menu == "Multas": gestao_multas()
elif menu == "Combustível": controle_combustivel()
# ... (manter as chamadas anteriores para Dashboard, Gestão, etc.)
