import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DO BANCO (CAMADA DE DADOS) ---
class DatabaseManager:
    def __init__(self, db_name="sgf_fleet.db"):
        self.db = db_name
        self.setup_tables()

    def execute_query(self, query, params=()):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def get_data(self, query, params=()):
        conn = sqlite3.connect(self.db)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df

    def setup_tables(self):
        # Criação das tabelas centrais com chaves estrangeiras
        queries = [
            """CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, login TEXT, senha TEXT, modulos_permissao TEXT)""",
            """CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, limite_revisao INTEGER, crlv TEXT)""",
            """CREATE TABLE IF NOT EXISTS motoristas (id INTEGER PRIMARY KEY, nome TEXT, cnh TEXT)""",
            """CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY, placa TEXT, status TEXT, custo REAL, aprovado BOOLEAN)""",
            """CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, acao TEXT, tabela TEXT, data_hora TIMESTAMP)"""
        ]
        def setup_user_table():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE,
        senha TEXT,
        modulos_permissao TEXT)""") # Ex: "Dashboard,Cadastro,Manutencao"
    conn.commit()
    conn.close()
        for q in queries: self.execute_query(q)

db = DatabaseManager()

# --- 2. SEGURANÇA E SESSÃO ---
if "user" not in st.session_state: st.session_state.user = None

def login_screen():
    st.title("🚛 SGF-Fleet Elite - Acesso")
    login = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Lógica de validação aqui
        st.session_state.user = {"login": login, "perm": ["Dashboard", "Cadastro"]}
        st.rerun()

if not st.session_state.user:
    login_screen()
    st.stop()

# --- 3. MÓDULOS DE NEGÓCIO ---
def render_dashboard():
    st.title("📊 Dashboard Executivo")
    col1, col2, col3 = st.columns(3)
    # KPIs interativos
    df_veiculos = db.get_data("SELECT * FROM veiculos")
    col1.metric("Frota Total", len(df_veiculos))
    # Gráficos e tabelas
    st.dataframe(df_veiculos)

def render_cadastro():
    st.title("📝 Cadastro de Ativos")
    # Formulario completo com edição e exclusão
    with st.form("cad_veiculo"):
        placa = st.text_input("Placa")
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            db.execute_query("INSERT INTO veiculos (placa, modelo) VALUES (?,?)", (placa, modelo))
            st.success("Veículo Cadastrado!")

# --- 4. NAVEGAÇÃO PRINCIPAL ---
st.sidebar.title(f"Olá, {st.session_state.user['login']}")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro", "Manutenção", "Checklist", "Abastecimentos", "Multas", "Motoristas"])

if menu == "Dashboard": render_dashboard()
elif menu == "Cadastro": render_cadastro()
# ... outros módulos seguem a mesma lógica ...
