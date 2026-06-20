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

elif menu == "Motoristas & Multimport streamlit as st
import sqlite3
import pandas as pd

# --- CLASSE DE GESTÃO DO SISTEMA ---
class FleetManager:
    def __init__(self):
        self.conn = sqlite3.connect("sgf_fleet_elite.db", check_same_thread=False)
        self._init_db()

    def _init_db(self):
        # Tabelas essenciais com chaves estrangeiras
        self.conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível')")
        self.conn.execute("CREATE TABLE IF NOT EXISTS motoristas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cnh TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, aprovado INTEGER DEFAULT 0)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista_id INTEGER, codigo TEXT, valor REAL)")
        self.conn.commit()

fm = FleetManager()

# --- INTERFACE ---
st.set_page_config(layout="wide", page_title="SGF-Fleet Elite")

# Menu de Navegação
menu = st.sidebar.radio("Módulos", ["Dashboard", "Frota", "Manutenção (OS)", "Motoristas/Multas"])

if menu == "Dashboard":
    st.title("📊 Dashboard Executivo")
    # Exemplo de consulta integrada
    df_v = pd.read_sql("SELECT * FROM veiculos", fm.conn)
    st.dataframe(df_v)

elif menu == "Frota":
    st.title("📝 Cadastro de Veículos")
    with st.form("form_veic"):
        placa = st.text_input("Placa")
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            fm.conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
            fm.conn.commit()
            st.success("Veículo salvo!")

elif menu == "Manutenção (OS)":
    st.title("🛠️ Gestão de OS")
    # Aqui o usuário abre a OS
    placas = pd.read_sql("SELECT placa FROM veiculos", fm.conn)['placa'].tolist()
    with st.form("os_form"):
        placa = st.selectbox("Selecione o Veículo", placas)
        servico = st.text_input("Descrição do serviço")
        custo = st.number_input("Custo R$")
        if st.form_submit_button("Abrir OS"):
            fm.conn.execute("INSERT INTO manutencao (placa, servico, custo, aprovado) VALUES (?,?,?,?)", (placa, servico, custo, 0))
            fm.conn.commit()
            st.success("OS enviada para aprovação!")

    # Área do Gestor para Aprovação
    st.subheader("Pendentes")
    pendentes = pd.read_sql("SELECT * FROM manutencao WHERE aprovado = 0", fm.conn)
    st.table(pendentes)

elif menu == "Motoristas/Multas":
    st.title("👤 Gestão de Multas e Motoristas")
    # Cadastro de motorista e registro de multa vinculado
    with st.form("multa_form"):
        nome = st.text_input("Nome do motorista")
        if st.form_submit_button("Cadastrar Motorista"):
            fm.conn.execute("INSERT INTO motoristas (nome) VALUES (?)", (nome,))
            fm.conn.commit()
            st.rerun()as":
    st.title("👤 Motoristas e Infrações")
    # Lógica de integração motorista/multa/CTB aqui...
