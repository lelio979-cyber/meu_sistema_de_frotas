import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Professional", layout="wide")
DB_NAME = "sgf_fleet.db"

# --- INICIALIZAÇÃO DE BANCO (Correção Automática) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Tabela de Veículos
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, 
        modelo TEXT, 
        motorista TEXT, 
        status TEXT, 
        km_atual INTEGER, 
        km_revisao INTEGER)""")
    # Tabela de Manutenção
    conn.execute("""CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        placa TEXT, 
        servico TEXT, 
        custo REAL, 
        data DATE)""")
    conn.commit()
    conn.close()

init_db()

# --- DASHBOARD ---
def dashboard():
    st.title("📊 Painel de Controle Corporativo")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    st.subheader("Frota Ativa e Alertas")
    if not df_v.empty:
        for _, veic in df_v.iterrows():
            diff = veic['km_revisao'] - veic['km_atual']
            alerta = " ⚠️ REVISÃO PRÓXIMA" if 0 < diff <= 500 else " 🚨 REVISÃO VENCIDA" if diff <= 0 else ""
            
            with st.expander(f"🚛 {veic['placa']} | {veic['modelo']}{alerta}"):
                c1, c2 = st.columns(2)
                c1.write(f"**KM Atual:** {veic['km_atual']} | **Meta Revisão:** {veic['km_revisao']}")
                if alerta: c1.error(f"Atenção: {alerta.strip()}")
                
                hist = df_os[df_os['placa'] == veic['placa']]
                if not hist.empty:
                    c2.dataframe(hist[['data', 'servico', 'custo']], use_container_width=True)
                else:
                    c2.info("Nenhuma manutenção registrada.")
    else:
        st.info("Nenhum veículo cadastrado.")

# --- MÓDULOS DE GESTÃO ---
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
            st.success("Veículo salvo!"); st.rerun()

def apontar_km():
    st.title("⏱️ Apontamento Rápido de KM")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    if not df.empty:
        with st.form("form_km"):
            placa = st.selectbox("Selecione o Veículo", df['placa'])
            novo_km = st.number_input("KM Atual", min_value=0)
            if st.form_submit_button("Atualizar"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (novo_km, placa))
                conn.commit(); conn.close(); st.success("Atualizado!"); st.rerun()
    else: st.info("Cadastre um veículo primeiro.")

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota", "Apontar KM"])
if menu == "Dashboard": dashboard()
elif menu == "Gestão de Frota": gestao_frota()
elif menu == "Apontar KM": apontar_km()
