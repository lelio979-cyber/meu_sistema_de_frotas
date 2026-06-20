import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "frota_base.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Tabela Veículos (já existente)
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

# Nova Tabela de Manutenção (OS)
    # Usamos FOREIGN KEY para garantir que a OS só exista se o veículo existir
    conn.execute("""CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        placa TEXT, 
        servico TEXT, 
        custo REAL, 
        data DATE,
        FOREIGN KEY(placa) REFERENCES veiculos(placa))""")
    
    conn.commit()
    conn.close()

init_db()

st.title("SGF-Fleet: Módulo de Manutenção")

# Opções de Menu
menu = st.sidebar.radio("Navegação", ["Cadastro de Veículos", "Lançar Manutenção"])

if menu == "Cadastro de Veículos":
    # ... (Seu código de cadastro do Passo 2) ...
    st.write("Módulo de Cadastro Ativo.")
    
elif menu == "Lançar Manutenção":
    st.subheader("Registrar Ordem de Serviço")
    
    # Buscar placas disponíveis para o selectbox
    conn = sqlite3.connect(DB_NAME)
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    with st.form("form_os"):
        placa = st.selectbox("Selecione o Veículo", veiculos['placa'] if not veiculos.empty else ["Nenhum"])
        servico = st.text_input("Descrição do Serviço")
        custo = st.number_input("Custo (R$)", min_value=0.0)
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("Salvar OS"):
            if placa != "Nenhum":
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO os (placa, servico, custo, data) VALUES (?, ?, ?, ?)", 
                             (placa, servico, custo, data))
                conn.commit()
                conn.close()
                st.success("OS lançada com sucesso!")
            else:
                st.error("Cadastre um veículo primeiro.")

# Exibir Histórico Global
st.divider()
st.subheader("Histórico Geral de Manutenções")
conn = sqlite3.connect(DB_NAME)
df_os = pd.read_sql("SELECT * FROM os", conn)
conn.close()
st.dataframe(df_os, use_container_width=True)
