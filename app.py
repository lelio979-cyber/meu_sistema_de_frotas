import streamlit as st
import sqlite3
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")

# 2. FUNÇÃO DE CONEXÃO E SETUP (Banco de Dados)
def get_db():
    return sqlite3.connect("frota.db")

def setup_db():
    conn = get_db()
    # Tabela Veículos com colunas extras
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, ano INTEGER, 
        renavam TEXT, seguro TEXT, km INTEGER)""")
    
    # Adicionando colunas de forma segura se o banco for antigo
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    cols = [c[1] for c in cursor.fetchall()]
    if 'ano' not in cols: conn.execute("ALTER TABLE veiculos ADD COLUMN ano INTEGER")
    if 'renavam' not in cols: conn.execute("ALTER TABLE veiculos ADD COLUMN renavam TEXT")
    if 'seguro' not in cols: conn.execute("ALTER TABLE veiculos ADD COLUMN seguro TEXT")
    
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL)")
    conn.commit()
    conn.close()

setup_db()
def setup_db():
    conn = get_db()
    # ... (suas tabelas existentes) ...
    conn.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        acao TEXT, 
        tabela TEXT, 
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()
# 1. LÓGICA DE LOGIN (SEGURANÇA)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔒 Acesso Restrito")
    senha_input = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha_input == "1234": # Troque '1234' pela sua senha secreta
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop() # Interrompe a execução do resto do app se não estiver logado

# A partir daqui, o código só roda se st.session_state["autenticado"] for True
# 3. INTERFACE PRINCIPAL
st.title("🚛 SGF-Fleet Elite Pro")
menu = st.sidebar.radio("Navegação", ["Cadastro", "Manutenção", "Dashboard"])

# 4. LÓGICA DO MENU CADASTRO
if menu == "Cadastro":
    st.subheader("Cadastro de Ativos")
    with st.form("form_cad"):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col1.text_input("Modelo")
        ano = col2.number_input("Ano", 2000, 2030)
        renavam = col1.text_input("Renavam")
        seguro = col2.text_input("Seguradora")
        km = st.number_input("KM Inicial", 0)
        
        if st.form_submit_button("Salvar Veículo"):
            conn = get_db()
            try:
                conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?)", 
                             (placa, modelo, ano, renavam, seguro, km))
                conn.commit()
                st.success("Veículo salvo!")
            except Exception as e: st.error(f"Erro: {e}")
            conn.close()

# 5. LÓGICA DO MENU MANUTENÇÃO
elif menu == "Manutenção":
    st.subheader("Registrar Manutenção")
    conn = get_db()
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not veiculos.empty:
        with st.form("form_os"):
            placa = st.selectbox("Selecione o Veículo", veiculos['placa'])
            servico = st.text_input("Serviço")
            custo = st.number_input("Custo (R$)", 0.0)
            if st.form_submit_button("Salvar OS"):
                conn = get_db()
                conn.execute("INSERT INTO os (placa, servico, custo) VALUES (?,?,?)", (placa, servico, custo))
                conn.commit()
                conn.close()
                st.success("OS salva!")
    else: st.warning("Cadastre um veículo primeiro.")

# 6. LÓGICA DO MENU DASHBOARD
elif menu == "Dashboard":
    st.subheader("Painel de Controle")
    conn = get_db()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    st.dataframe(df_v)
