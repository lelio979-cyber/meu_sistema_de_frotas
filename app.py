import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Gestão de Frota Pro", layout="wide")

def get_db():
    conn = sqlite3.connect("frota.db")
    return conn

def setup():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL)")
    
    # Nova tabela de combustíveis
    conn.execute("CREATE TABLE IF NOT EXISTS combustivel (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, litros REAL, km_rodado REAL)")
    conn.commit()
    conn.close()

setup()

st.title("🚛 Gestão de Frota")
menu = st.sidebar.radio("Menu", ["Cadastro", "Manutenção", "Combustível", "Dashboard"])

if menu == "Cadastro":
    st.subheader("Novo Veículo")
    with st.form("form_cad"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Inicial", 0)
        if st.form_submit_button("Salvar"):
            conn = get_db()
            try:
                conn.execute("INSERT INTO veiculos VALUES (?, ?, ?)", (placa, modelo, km))
                conn.commit()
                st.success("Veículo salvo!")
            except: st.error("Erro ao salvar.")
            conn.close()

elif menu == "Manutenção":
    st.subheader("Registrar Manutenção")
    conn = get_db()
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not veiculos.empty:
        with st.form("form_os"):
            placa = st.selectbox("Veículo", veiculos['placa'])
            servico = st.text_input("Serviço Realizado")
            custo = st.number_input("Custo (R$)", 0.0)
            if st.form_submit_button("Salvar OS"):
                conn = get_db()
                conn.execute("INSERT INTO os (placa, servico, custo) VALUES (?, ?, ?)", (placa, servico, custo))
                conn.commit()
                conn.close()
                st.success("OS registrada!")
    else: st.warning("Cadastre um veículo antes.")

elif menu == "Dashboard":
    st.subheader("Painel de Performance e Alertas")
    
    conn = get_db()
    # Puxamos os dados dos veículos para verificar o KM
    df_v = pd.read_sql("SELECT placa, modelo, km FROM veiculos", conn)
    conn.close()
    
    st.write("### 🚨 Alertas de Revisão")
    
    # Lógica de Alerta (Exemplo: limite de 10.000 KM para revisão)
    LIMITE_REVISAO = 10000 
    
    veiculos_criticos = df_v[df_v['km'] >= LIMITE_REVISAO]
    
    if not veiculos_criticos.empty:
        for _, row in veiculos_criticos.iterrows():
            st.error(f"⚠️ Atenção: O veículo {row['placa']} ({row['modelo']}) atingiu {row['km']} KM e precisa de revisão urgente!")
    else:
        st.success("✅ Todos os veículos estão com a manutenção em dia.")
        
    st.divider()
    st.write("### Frota Geral")
    st.dataframe(df_v)

# --- NOVO MÓDULO ---
if menu == "Combustível":
    st.subheader("Registrar Abastecimento")
    conn = get_db()
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not veiculos.empty:
        with st.form("form_comb"):
            placa = st.selectbox("Veículo", veiculos['placa'])
            litros = st.number_input("Litros Abastecidos", 0.1)
            km_rodado = st.number_input("KM Rodado desde último abastecimento", 0.1)
            if st.form_submit_button("Salvar Combustível"):
                conn = get_db()
                conn.execute("INSERT INTO combustivel (placa, litros, km_rodado) VALUES (?, ?, ?)", (placa, litros, km_rodado))
                conn.commit()
                conn.close()
                media = km_rodado / litros
                st.success(f"Média calculada: {media:.2f} KM/L!")
    else: st.warning("Cadastre um veículo primeiro.")

elif menu == "Dashboard":
    st.subheader("Painel Geral")
    conn = get_db()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_comb = pd.read_sql("SELECT * FROM combustivel", conn)
    conn.close()
    st.write("### Consumo de Combustível")
    st.dataframe(df_comb)
