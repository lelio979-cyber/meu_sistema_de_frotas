import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E ENGINE DE DADOS ---
class FleetManager:
    def __init__(self):
        self.conn = sqlite3.connect("sgf_fleet_elite.db", check_same_thread=False)
        self._init_db()

    def _init_db(self):
        # Tabelas Core
        self.conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, permissao TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, status TEXT DEFAULT 'Disponível')")
        self.conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, aprovado INTEGER DEFAULT 0)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS cartoes (id INTEGER PRIMARY KEY, nome TEXT, saldo REAL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, codigo TEXT, valor REAL)")
        self.conn.commit()

fm = FleetManager()

# --- SEGURANÇA ---
st.set_page_config(layout="wide", page_title="SGF-Fleet Elite")
if "user" not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.title("🚛 SGF-Fleet Elite - Login")
    login = st.text_input("Usuário")
    if st.button("Entrar"):
        st.session_state.user = {"login": login}
        st.rerun()
    st.stop()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Módulos", ["Dashboard", "Frota", "Manutenção (OS)", "Aprovações", "Cartão Combustível", "Multas"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    col1, col2 = st.columns(2)
    col1.metric("Frota Ativa", len(pd.read_sql("SELECT * FROM veiculos", fm.conn)))
    col2.metric("OS Pendentes", len(pd.read_sql("SELECT * FROM manutencao WHERE aprovado=0", fm.conn)))

# --- FROTA ---
elif menu == "Frota":
    st.title("📝 Gestão de Veículos")
    with st.form("cad_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            fm.conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
            fm.conn.commit()
            st.success("Veículo cadastrado!")

# --- MANUTENÇÃO ---
elif menu == "Manutenção (OS)":
    st.title("🛠️ Abertura de OS")
    placas = pd.read_sql("SELECT placa FROM veiculos WHERE status='Disponível'", fm.conn)['placa'].tolist()
    with st.form("os_form"):
        placa = st.selectbox("Selecione Veículo", placas)
        servico = st.text_input("Serviço")
        custo = st.number_input("Custo R$")
        if st.form_submit_button("Abrir OS"):
            fm.conn.execute("INSERT INTO manutencao (placa, servico, custo) VALUES (?,?,?)", (placa, servico, custo))
            fm.conn.execute("UPDATE veiculos SET status = 'Em Manutenção' WHERE placa = ?", (placa,))
            fm.conn.commit()
            st.success("OS enviada!")

# --- APROVAÇÕES ---
elif menu == "Aprovações":
    st.title("✅ Aprovação Financeira")
    pendentes = pd.read_sql("SELECT * FROM manutencao WHERE aprovado = 0", fm.conn)
    for i, row in pendentes.iterrows():
        if st.button(f"Aprovar OS {row['id']} - {row['placa']} (R$ {row['custo']})"):
            fm.conn.execute("UPDATE manutencao SET aprovado = 1 WHERE id = ?", (row['id'],))
            fm.conn.execute("UPDATE veiculos SET status = 'Disponível' WHERE placa = ?", (row['placa'],))
            fm.conn.commit()
            st.rerun()

# --- CARTÃO COMBUSTÍVEL ---
elif menu == "Cartão Combustível":
    st.title("💳 Gestão de Cartões")
    saldo = pd.read_sql("SELECT SUM(saldo) as s FROM cartoes", fm.conn)['s'].iloc[0] or 0
    st.metric("Saldo Global", f"R$ {saldo:,.2f}")

# --- MULTAS ---
elif menu == "Multas":
    st.title("🚦 Módulo de Multas")
    with st.form("multa"):
        placa = st.text_input("Placa")
        codigo = st.text_input("Código CTB")
        if st.form_submit_button("Registrar"):
            fm.conn.execute("INSERT INTO multas (placa, codigo, valor) VALUES (?,?,?)", (placa, codigo, 0))
            fm.conn.commit()
            st.success("Multa lançada.")
