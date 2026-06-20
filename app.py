import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "frota_base.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Garantindo as tabelas
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, data DATE)")
    conn.commit()
    conn.close()

init_db()

st.title("SGF-Fleet: Módulo de Apontamento KM")

menu = st.sidebar.radio("Navegação", ["Cadastro de Veículos", "Lançar Manutenção", "Apontar KM"])

# --- LÓGICA DO NOVO MÓDULO ---
if menu == "Apontar KM":
    st.subheader("Atualizar Quilometragem")
    conn = sqlite3.connect(DB_NAME)
    df_veiculos = pd.read_sql("SELECT placa, km_atual FROM veiculos", conn)
    conn.close()

    if not df_veiculos.empty:
        with st.form("form_km"):
            placa = st.selectbox("Selecione o Veículo", df_veiculos['placa'])
            novo_km = st.number_input("Novo KM Atual", min_value=0)
            if st.form_submit_button("Atualizar KM"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (novo_km, placa))
                conn.commit()
                conn.close()
                st.success(f"KM do veículo {placa} atualizado para {novo_km}!")
                st.rerun()
    else:
        st.info("Cadastre um veículo primeiro.")

elif menu == "Cadastro de Veículos":
    st.write("Módulo de Cadastro Ativo.")
    # ... (seu código anterior do passo 2) ...

elif menu == "Lançar Manutenção":
    st.write("Módulo de Manutenção Ativo.")
    # ... (seu código anterior do passo 3) ...
