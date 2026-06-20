import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. ENGINE DE DADOS ---
class FleetSystem:
    def __init__(self):
        self.conn = sqlite3.connect("sgf_fleet.db", check_same_thread=False)
        self.setup_tables()

    def setup_tables(self):
        # Tabelas com chaves estrangeiras para garantir integridade
        self.conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, status TEXT DEFAULT 'Disponível')")
        self.conn.execute("CREATE TABLE IF NOT EXISTS motoristas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cnh TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, aprovado INTEGER DEFAULT 0, FOREIGN KEY(placa) REFERENCES veiculos(placa))")
        self.conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, codigo_infracao TEXT, valor REAL, motorista_id INTEGER)")
        self.conn.commit()

db = FleetSystem()

# --- 2. INTERFACE (FRONTEND) ---
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Frota", "Manutenção", "Multas"])

if menu == "Dashboard":
    st.title("📊 Painel Executivo")
    df_frota = pd.read_sql("SELECT * FROM veiculos", db.conn)
    st.metric("Veículos Ativos", len(df_frota))
    st.dataframe(df_frota)

elif menu == "Frota":
    st.title("📝 Cadastro de Veículos")
    with st.form("cad_frota"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar Veículo"):
            db.conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
            db.conn.commit()
            st.success("Veículo cadastrado!")

elif menu == "Manutenção":
    st.title("🛠️ Controle de Manutenção")
    # Filtra apenas veículos disponíveis
    placas = pd.read_sql("SELECT placa FROM veiculos WHERE status='Disponível'", db.conn)['placa'].tolist()
    with st.form("os_form"):
        placa = st.selectbox("Selecione o Veículo", placas)
        servico = st.text_input("Descrição do Serviço")
        custo = st.number_input("Custo R$")
        if st.form_submit_button("Abrir OS"):
            db.conn.execute("INSERT INTO manutencao (placa, servico, custo) VALUES (?,?,?)", (placa, servico, custo))
            db.conn.execute("UPDATE veiculos SET status = 'Em Manutenção' WHERE placa = ?", (placa,))
            db.conn.commit()
            st.success("OS Aberta e veículo bloqueado!")

elif menu == "Multas":
    st.title("🚦 Registro de Infrações")
    placas = pd.read_sql("SELECT placa FROM veiculos", db.conn)['placa'].tolist()
    with st.form("multa_form"):
        placa = st.selectbox("Veículo", placas)
        codigo = st.text_input("Código da Infração (CTB)")
        if st.form_submit_button("Registrar Multa"):
            # Aqui entrará a lógica de buscar o valor no dicionário CTB
            db.conn.execute("INSERT INTO multas (placa, codigo_infracao, valor) VALUES (?,?,?)", (placa, codigo, 150.00))
            db.conn.commit()
            st.success("Multa registrada.")
