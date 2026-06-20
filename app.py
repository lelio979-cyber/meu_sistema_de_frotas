import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Elite Pro", layout="wide")
DB_NAME = "sgf_fleet_elite.db"

# --- BANCO DE DADOS (Estrutura Robusta) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Tabela Veículos
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, 
        km_atual INTEGER, km_revisao INTEGER)""")
    # Tabela Manutenção (OS)
    conn.execute("""CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, 
        servico TEXT, custo REAL, data DATE)""")
    conn.commit(); conn.close()

init_db()

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Painel de Performance (Elite Pro)")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    st.subheader("Frota Ativa e Indicadores")
    if not df_v.empty:
        for _, veic in df_v.iterrows():
            total_custo = df_os[df_os['placa'] == veic['placa']]['custo'].sum()
            custo_km = total_custo / veic['km_atual'] if veic['km_atual'] > 0 else 0
            
            with st.expander(f"🚛 {veic['placa']} | {veic['modelo']} (Motorista: {veic['motorista']})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("KM Atual", f"{veic['km_atual']:,}")
                c2.metric("Custo Manutenção", f"R$ {total_custo:,.2f}")
                c3.metric("Eficiência (Custo/KM)", f"R$ {custo_km:.2f}")
                
                if veic['km_atual'] >= veic['km_revisao']:
                    st.error(f"🚨 ALERTA: Veículo {veic['placa']} com revisão vencida!")
    else:
        st.info("Nenhum veículo cadastrado.")

def gestao_frota():
    st.title("🚛 Cadastro de Ativos")
    with st.form("form_veic", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        motorista = col1.text_input("Motorista")
        km = col2.number_input("KM Atual", min_value=0)
        km_rev = col1.number_input("KM Próxima Revisão", min_value=0)
        
        if st.form_submit_button("Registrar Ativo"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?)", 
                         (placa, modelo, motorista, km, km_rev))
            conn.commit(); conn.close()
            st.success("Ativo registrado!"); st.rerun()

def lancar_os():
    st.title("🛠️ Lançar Ordem de Serviço")
    conn = sqlite3.connect(DB_NAME)
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    with st.form("form_os"):
        placa = st.selectbox("Veículo", veiculos['placa'])
        servico = st.text_input("Serviço")
        custo = st.number_input("Custo (R$)", min_value=0.0)
        if st.form_submit_button("Lançar OS"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO os (placa, servico, custo, data) VALUES (?,?,?,?)", 
                         (placa, servico, custo, pd.Timestamp.now().date()))
            conn.commit(); conn.close()
            st.success("OS lançada!"); st.rerun()

def apontar_km():
    st.title("⏱️ Apontamento Rápido de KM")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT placa FROM veiculos", conn)
    conn.close()
    
    with st.form("form_km"):
        placa = st.selectbox("Selecione o Veículo", df['placa'])
        novo_km = st.number_input("Novo KM", min_value=0)
        if st.form_submit_button("Atualizar KM"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (novo_km, placa))
            conn.commit(); conn.close()
            st.success("KM Atualizado!"); st.rerun()

def exportar_relatorio():
    st.title("📥 Relatório Gerencial")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    st.download_button("Baixar Relatório (CSV)", df.to_csv(index=False), "frota_relatorio.csv", "text/csv")
    st.dataframe(df, use_container_width=True)

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Dashboard",
