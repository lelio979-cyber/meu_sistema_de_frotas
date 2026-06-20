import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. ENGINE DE DADOS (SQLITE CENTRAL) ---
class DatabaseEngine:
    def __init__(self, db_path="sgf_fleet_elite.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS usuarios 
            (login TEXT PRIMARY KEY, senha TEXT, modulos TEXT)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS veiculos 
            (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, crlv TEXT, status TEXT DEFAULT 'Disponível')""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS manutencao 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, aprovado INTEGER DEFAULT 0)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS multas 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista_id INTEGER, codigo TEXT, valor REAL)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS motoristas 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cnh TEXT)""")
        self.conn.commit()

db = DatabaseEngine()

# --- 2. GERENCIAMENTO DE ESTADO ---
if "user" not in st.session_state: st.session_state.user = None

# --- 3. INTERFACE PRINCIPAL ---
st.set_page_config(layout="wide", page_title="SGF-Fleet Elite")

# Login simples
if not st.session_state.user:
    st.title("🚛 SGF-Fleet Elite - Login")
    login = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Aqui a validação real seria feita no banco
        st.session_state.user = {"login": login, "perm": "admin"}
        st.rerun()
    st.stop()

# Navegação
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota", "Manutenção (OS)", "Motoristas & Multas"])

# --- 4. LÓGICA POR MÓDULO ---
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    # Colocar métricas e gráficos aqui...
    st.write("Bem-vindo, sistema operacional ativo.")

elif menu == "Gestão de Frota":
    st.title("📝 Cadastro e Controle")
    with st.form("veiculo_form"):
        placa = st.text_input("Placa")
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar Veículo"):
            db.conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
            db.conn.commit()
            st.success("Veículo salvo!")

elif menu == "Manutenção (OS)":
    st.title("🛠️ Controle de OS")
    # Lógica de aprovação de custos aqui...

elif menu == "Motoristas & Multas":
    st.title("👤 Motoristas e Infrações")
    # Lógica de integração motorista/multa/CTB aqui...
