import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Professional", layout="wide")
DB_NAME = "sgf_fleet.db"

# --- INICIALIZAÇÃO DE BANCO (Garante estrutura única) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Adicionamos 'km_revisao' para o controle preventivo
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, 
        status TEXT, km_atual INTEGER, km_revisao INTEGER)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, 
        servico TEXT, custo REAL, data DATE)""")
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
    conn.close()
    
    st.subheader("Estado da Frota e Alertas")
    
    for _, veic in df_v.iterrows():
        # Cálculo de alerta (se faltarem menos de 500km para a revisão)
        diff = veic['km_revisao'] - veic['km_atual']
        alerta = ""
        if diff <= 500 and diff > 0:
            alerta = " ⚠️ REVISÃO PRÓXIMA"
        elif diff <= 0:
            alerta = " 🚨 REVISÃO VENCIDA"
            
        with st.expander(f"🚛 {veic['placa']} | {veic['modelo']}{alerta}"):
            st.write(f"**KM Atual:** {veic['km_atual']} | **Próxima Revisão:** {veic['km_revisao']}")
            if alerta:
                st.error(f"Atenção: O veículo {veic['placa']} requer atenção imediata!")

# --- GESTÃO DE FROTA ---
def gestao_frota():
    st.title("🚛 Gestão de Ativos")
    with st.form("form_veic", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        km = col1.number_input("KM Atual", min_value=0)
        km_rev = col2.number_input("KM Próxima Revisão", min_value=0)
        
        if st.form_submit_button("Salvar Veículo"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, km_atual, km_revisao) VALUES (?,?,?,?)", 
                         (placa, modelo, km, km_rev))
            conn.commit(); conn.close()
            st.success("Veículo salvo!")
            st.rerun()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota"])
if menu == "Dashboard": dashboard()
else: gestao_frota()
