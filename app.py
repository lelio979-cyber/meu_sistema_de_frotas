import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Fleet Pro ERP", layout="wide")
conn = sqlite3.connect("sgf_erp.db", check_same_thread=False)

# Criação de todas as tabelas necessárias
tables = {
    "frota": "id INTEGER PRIMARY KEY, placa TEXT, modelo TEXT",
    "abastecimento": "id INTEGER PRIMARY KEY, id_veiculo INTEGER, km REAL, litros REAL, valor REAL, data TEXT",
    "manutencao": "id INTEGER PRIMARY KEY, id_veiculo INTEGER, descricao TEXT, custo REAL, data TEXT",
    "cartoes": "id INTEGER PRIMARY KEY, nome_cartao TEXT, limite REAL",
    "trechos": "id INTEGER PRIMARY KEY, id_veiculo INTEGER, origem TEXT, destino TEXT, km_rodado REAL, motorista TEXT",
    "checklist": "id INTEGER PRIMARY KEY, id_veiculo INTEGER, pneus TEXT, luzes TEXT, oleo TEXT, observacao TEXT, data TEXT"
}
for table, cols in tables.items():
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")

# --- MENU LATERAL ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro Veículos", "Abastecimento", "Ordens de Serviço", "Checklist", "Trechos/Viagens", "Gestão Cartões"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    # Exemplo de Relatório Cruzado
    df_abast = pd.read_sql("SELECT * FROM abastecimento", conn)
    if not df_abast.empty:
        st.metric("Total Gasto em Combustível", f"R$ {df_abast['valor'].sum():,.2f}")
    st.info("Aqui você pode inserir gráficos com a biblioteca Plotly.")

# --- MÓDULOS DE CADASTRO E MOVIMENTAÇÃO ---
elif menu == "Cadastro Veículos":
    st.title("➕ Cadastro de Veículos")
    with st.form("f_veiculo"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT INTO frota (placa, modelo) VALUES (?,?)", (placa, modelo))
            conn.commit()
            st.success("Veículo salvo!")

elif menu == "Abastecimento":
    st.title("⛽ Abastecimento")
    with st.form("f_abast"):
        id_v = st.number_input("ID Veículo", min_value=1)
        km = st.number_input("KM Atual")
        litros = st.number_input("Litros")
        valor = st.number_input("Valor R$")
        if st.form_submit_button("Registrar"):
            conn.execute("INSERT INTO abastecimento (id_veiculo, km, litros, valor, data) VALUES (?,?,?,?,?)", (id_v, km, litros, valor, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Registrado!")

elif menu == "Ordens de Serviço":
    st.title("🛠️ Ordens de Serviço (Manutenção)")
    with st.form("f_os"):
        id_v = st.number_input("ID Veículo")
        desc = st.text_area("Descrição do Serviço")
        custo = st.number_input("Custo R$")
        if st.form_submit_button("Abrir OS"):
            conn.execute("INSERT INTO manutencao (id_veiculo, descricao, custo, data) VALUES (?,?,?,?)", (id_v, desc, custo, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success("OS Registrada!")

elif menu == "Checklist":
    st.title("✅ Checklist Diário")
    with st.form("f_check"):
        id_v = st.number_input("ID Veículo")
        pneus = st.selectbox("Estado Pneus", ["Bom", "Ruim"])
        luzes = st.selectbox("Estado Luzes", ["OK", "Defeito"])
        obs = st.text_area("Observações")
        if st.form_submit_button("Finalizar Checklist"):
            conn.execute("INSERT INTO checklist (id_veiculo, pneus, luzes, observacao, data) VALUES (?,?,?,?,?)", (id_v, pneus, luzes, obs, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Checklist salvo!")

elif menu == "Trechos/Viagens":
    st.title("📍 Registro de Trechos")
    with st.form("f_trecho"):
        id_v = st.number_input("ID Veículo")
        origem = st.text_input("Origem")
        destino = st.text_input("Destino")
        motorista = st.text_input("Motorista")
        if st.form_submit_button("Salvar Viagem"):
            conn.execute("INSERT INTO trechos (id_veiculo, origem, destino, motorista) VALUES (?,?,?,?)", (id_v, origem, destino, motorista))
            conn.commit()
            st.success("Viagem registrada!")

elif menu == "Gestão Cartões":
    st.title("💳 Cartões Combustível")
    with st.form("f_cartao"):
        nome = st.text_input("Nome do Cartão")
        limite = st.number_input("Limite R$")
        if st.form_submit_button("Cadastrar"):
            conn.execute("INSERT INTO cartoes (nome_cartao, limite) VALUES (?,?)", (nome, limite))
            conn.commit()
            st.success("Cartão salvo!")
