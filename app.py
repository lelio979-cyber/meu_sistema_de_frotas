import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO DE DADOS ---
st.set_page_config(page_title="SGF-Fleet Pro ERP", layout="wide")
conn = sqlite3.connect("sgf_erp.db", check_same_thread=False)

# Tabelas necessárias para os novos módulos
conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY, placa TEXT, modelo TEXT, custo REAL)")
conn.execute("CREATE TABLE IF NOT EXISTS abastecimento (id INTEGER PRIMARY KEY, id_veiculo INTEGER, km REAL, litros REAL, valor REAL, data TEXT)")
conn.commit()

# --- SIDEBAR: MENU DE NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro Veículos", "Abastecimento", "Ordens de Serviço"])

# --- MÓDULO: DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    df = pd.read_sql("SELECT * FROM frota", conn)
    if not df.empty:
        st.metric("Total Veículos", len(df))
        st.metric("Custo Total (Manutenções)", f"R$ {df['custo'].sum():,.2f}")
    else:
        st.info("Cadastre veículos para ver o painel.")

# --- MÓDULO: CADASTRO ---
elif menu == "Cadastro Veículos":
    st.title("➕ Cadastro de Frota")
    with st.form("form_veiculo"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        custo = st.number_input("Custo Inicial", value=0.0)
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT INTO frota (placa, modelo, custo) VALUES (?,?,?)", (placa, modelo, custo))
            conn.commit()
            st.success("Veículo cadastrado!")

# --- MÓDULO: ABASTECIMENTO ---
elif menu == "Abastecimento":
    st.title("⛽ Controle de Abastecimento")
    veiculos = pd.read_sql("SELECT id, placa FROM frota", conn)
    
    with st.form("form_abast"):
        v_id = st.selectbox("Selecione o Veículo", veiculos['id'].tolist(), format_func=lambda x: veiculos[veiculos['id']==x]['placa'].values[0])
        km = st.number_input("Hodômetro")
        litros = st.number_input("Litros")
        valor = st.number_input("Valor Total (R$)")
        if st.form_submit_button("Registrar"):
            conn.execute("INSERT INTO abastecimento (id_veiculo, km, litros, valor, data) VALUES (?,?,?,?,?)", 
                         (v_id, km, litros, valor, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Abastecimento registrado!")

# --- MÓDULO: ORDENS DE SERVIÇO (Exemplo de expansão) ---
elif menu == "Ordens de Serviço":
    st.title("🛠️ Ordens de Serviço")
    st.warning("Módulo em desenvolvimento. Siga o padrão dos anteriores para expandir!")
