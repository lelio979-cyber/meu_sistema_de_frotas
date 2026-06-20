import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- ENGINE CENTRAL ---
class FleetSystem:
    def __init__(self):
        self.conn = sqlite3.connect("sgf_fleet.db", check_same_thread=False)
        self.setup_tables()

    def setup_tables(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, status TEXT DEFAULT 'Disponível')")
        self.conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, aprovado INTEGER DEFAULT 0)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, codigo TEXT, valor REAL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, acao TEXT, data TIMESTAMP)")
        self.conn.commit()

    def log(self, usuario, acao):
        self.conn.execute("INSERT INTO auditoria (usuario, acao, data) VALUES (?,?,?)", (usuario, acao, datetime.now()))
        self.conn.commit()

db = FleetSystem()

# --- INTERFACE CENTRALIZADA ---
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")

# Menu de Navegação - ONDE A MÁGICA DE APARECER ACONTECE
menu = st.sidebar.radio("Navegação", ["Dashboard", "Frota", "Manutenção", "Multas", "Auditoria"])

if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    col1, col2 = st.columns(2)
    col1.metric("Veículos", len(pd.read_sql("SELECT * FROM veiculos", db.conn)))
    col2.metric("Manutenções Pendentes", len(pd.read_sql("SELECT * FROM manutencao WHERE aprovado=0", db.conn)))

elif menu == "Frota":
    st.title("📝 Gestão de Veículos")
    with st.form("f"):
        placa = st.text_input("Placa")
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            db.conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
            db.conn.commit()
            db.log("Admin", f"Cadastrou veículo {placa}")
            st.success("Salvo!")

elif menu == "Manutenção":
    st.title("🛠️ Módulo de Manutenção")
    # Aqui você vê o formulário e a lista
    df = pd.read_sql("SELECT * FROM manutencao", db.conn)
    st.dataframe(df)
    
    with st.form("m"):
        placa = st.text_input("Placa do Veículo")
        servico = st.text_input("Serviço")
        custo = st.number_input("Custo")
        if st.form_submit_button("Abrir OS"):
            db.conn.execute("INSERT INTO manutencao (placa, servico, custo) VALUES (?,?,?)", (placa, servico, custo))
            db.conn.commit()
            db.log("Admin", f"Abriu OS para {placa}")
            st.rerun()

elif menu == "Multas":
    st.title("🚦 Registro de Multas")
    with st.form("m_form"):
        placa = st.text_input("Placa")
        codigo = st.text_input("Código CTB")
        if st.form_submit_button("Lançar"):
            db.conn.execute("INSERT INTO multas (placa, codigo, valor) VALUES (?,?,?)", (placa, codigo, 150.0))
            db.conn.commit()
            db.log("Admin", f"Lançou multa para {placa}")
            st.rerun()

elif menu == "Auditoria":
    st.title("📜 Logs do Sistema")
    st.dataframe(pd.read_sql("SELECT * FROM auditoria ORDER BY data DESC", db.conn))
