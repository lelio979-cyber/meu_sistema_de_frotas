import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SGF-Fleet Professional", layout="wide")
DB_NAME = "sgf_fleet.db"

# --- CORREÇÃO AUTOMÁTICA DE ESTRUTURA ---
def fix_db_structure():
    conn = sqlite3.connect(DB_NAME)
    # Garante que a tabela tenha exatamente as colunas que o código espera
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, status TEXT, km_atual INTEGER, km_revisao INTEGER)")
    # Verifica se as colunas existem, caso contrário tenta adicionar
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'km_revisao' not in cols:
        conn.execute("ALTER TABLE veiculos ADD COLUMN km_revisao INTEGER DEFAULT 0")
    conn.commit()
    conn.close()

fix_db_structure()

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Painel de Controle")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df_v.empty:
        for _, veic in df_v.iterrows():
            diff = veic['km_revisao'] - veic['km_atual']
            alerta = " ⚠️ REVISÃO PRÓXIMA" if 0 < diff <= 500 else " 🚨 REVISÃO VENCIDA" if diff <= 0 else ""
            
            with st.expander(f"🚛 {veic['placa']} | {veic['modelo']}{alerta}"):
                st.write(f"**KM Atual:** {veic['km_atual']} | **Próxima Revisão:** {veic['km_revisao']}")
    else:
        st.info("Nenhum veículo cadastrado.")

def gestao_frota():
    st.title("🚛 Gestão de Ativos")
    with st.form("form_veic", clear_on_submit=True):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        km = st.number_input("KM Atual", min_value=0)
        km_rev = st.number_input("KM Próxima Revisão", min_value=0)
        
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, km_atual, km_revisao) VALUES (?,?,?,?)", (placa, modelo, km, km_rev))
            conn.commit(); conn.close()
            st.success("Salvo!")
            st.rerun()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota"])
if menu == "Dashboard": dashboard()
else: gestao_frota()
