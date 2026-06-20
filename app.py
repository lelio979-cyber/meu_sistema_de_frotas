import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Professional", layout="wide")
DB_NAME = "sgf_fleet.db"

# --- INICIALIZAÇÃO DE BANCO (Garante estrutura única) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Criamos a tabela com as 6 colunas exatas que definimos
    conn.execute("DROP TABLE IF EXISTS veiculos") 
    conn.execute("""CREATE TABLE veiculos (
        placa TEXT PRIMARY KEY, 
        modelo TEXT, 
        motorista TEXT, 
        status TEXT, 
        km_atual INTEGER, 
        extra TEXT)""")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, data DATE)")
    conn.commit()
    conn.close()

# Executa apenas uma vez para limpar duplicatas e corrigir estrutura
if 'db_inicializado' not in st.session_state:
    init_db()
    st.session_state['db_inicializado'] = True

# --- DASHBOARD ---
def dashboard():
    st.title("📊 Painel de Controle Corporativo")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    if not df_v.empty:
        for _, veic in df_v.iterrows():
            with st.expander(f"🚛 Placa: {veic['placa']} | Modelo: {veic['modelo']} | Status: {veic['status']}"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**Motorista:** {veic['motorista']}")
                col_a.write(f"**KM Atual:** {veic['km_atual']}")
                
                historico = df_os[df_os['placa'] == veic['placa']]
                if not historico.empty:
                    col_b.dataframe(historico[['data', 'servico', 'custo']], use_container_width=True)
                else:
                    col_b.info("Sem manutenções.")
    else:
        st.info("Nenhum veículo cadastrado.")

# --- GESTÃO DE FROTA ---
def gestao_frota():
    st.title("🚛 Gestão de Ativos")
    with st.form("form_veic", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa (Ex: ABC-1234)").upper()
        modelo = col2.text_input("Modelo")
        motorista = col1.text_input("Motorista")
        status = col2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        km = col1.number_input("KM Atual", min_value=0)
        
        if st.form_submit_button("Salvar Veículo"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO veiculos VALUES (?,?,?,?,?,?)", (placa, modelo, motorista, status, km, None))
            conn.commit()
            conn.close()
            st.success("Veículo cadastrado!")
            st.rerun()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota"])
if menu == "Dashboard": dashboard()
else: gestao_frota()
