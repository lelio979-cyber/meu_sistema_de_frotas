import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")

def init_db():
    conn = sqlite3.connect('frotas_pro.db', check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS motoristas (nome TEXT PRIMARY KEY, cnh TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS checklists (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, km INTEGER, data TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS ordens_servico (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, descricao TEXT, custo REAL, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL, tipo_custo TEXT, data TEXT)")
    conn.commit()
    return conn

conn = init_db()

# --- MÓDULO DE ALERTAS (INTEGRADO) ---
def mod_alertas_inteligentes():
    st.subheader("🚨 Painel de Alertas Operacionais")
    
    # Lógica de análise de dados
    os_pendentes = pd.read_sql("SELECT COUNT(*) FROM ordens_servico WHERE status = 'Aberta'", conn).iloc[0,0]
    veiculos_alerta = pd.read_sql("SELECT placa FROM veiculos WHERE km_atual > 9000", conn)
    
    col_a, col_b = st.columns(2)
    
    if os_pendentes > 0:
        col_a.warning(f"⚠️ {os_pendentes} O.S. aguardando finalização.")
    else:
        col_a.success("✅ Nenhuma O.S. pendente.")
        
    if not veiculos_alerta.empty:
        col_b.error(f"🔧 {len(veiculos_alerta)} veículo(s) próximo da revisão!")
    else:
        col_b.success("✅ Frota com revisão em dia.")

# --- MÓDULOS ---
def mod_dashboard():
    st.header("📊 Painel Estratégico")
    # Chamada do novo painel de alertas
    mod_alertas_inteligentes()
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Custo Total", "R$ 28.400", "5%")
    col2.metric("Veículos Ativos", "15", "0")
    col3.metric("Eficiência", "8.2 km/L", "0.5")
    
    df = pd.read_sql("SELECT * FROM financeiro", conn)
    if not df.empty:
        fig = px.bar(df, x='data', y='valor', title="Tendência de Gastos")
        st.plotly_chart(fig, use_container_width=True)

# ... (Módulos de mod_veiculos, mod_motoristas, mod_checklist, mod_os, mod_abastecimento, mod_auditoria permanecem iguais) ...

def mod_veiculos():
    st.header("🚗 Gestão de Veículos")
    with st.form("v"):
        p = st.text_input("Placa"); m = st.text_input("Modelo"); k = st.number_input("KM")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?)", (p, m, k))
            conn.commit(); st.success("Veículo salvo!")
    st.dataframe(pd.read_sql("SELECT * FROM veiculos", conn))

def mod_motoristas():
    st.header("👤 Motoristas")
    with st.form("m"):
        n = st.text_input("Nome"); c = st.text_input("CNH")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO motoristas VALUES (?,?)", (n, c))
            conn.commit(); st.success("Salvo!")
    st.dataframe(pd.read_sql("SELECT * FROM motoristas", conn))

def mod_checklist():
    st.header("📝 Checklist de Campo")
    with st.form("c"):
        placa = st.text_input("Placa"); mot = st.text_input("Motorista"); km = st.number_input("KM")
        if st.form_submit_button("Registrar"):
            conn.execute("INSERT INTO checklists (placa, motorista, km, data) VALUES (?,?,?,?)", (placa, mot, km, datetime.now()))
            conn.commit(); st.success("Registrado!")
    st.dataframe(pd.read_sql("SELECT * FROM checklists", conn))

def mod_os():
    st.header("🛠️ Ordens de Serviço")
    with st.form("os"):
        placa = st.text_input("Placa"); desc = st.text_area("Descrição"); cust = st.number_input("Custo")
        if st.form_submit_button("Abrir OS"):
            conn.execute("INSERT INTO ordens_servico (placa, descricao, custo, status) VALUES (?,?,?,?)", (placa, desc, cust, 'Aberta'))
            conn.commit(); st.success("OS Aberta!")
    st.dataframe(pd.read_sql("SELECT * FROM ordens_servico", conn))

def mod_abastecimento():
    st.header("⛽ Abastecimento")
    val = st.number_input("Valor"); data = st.date_input("Data")
    if st.button("Registrar"):
        conn.execute("INSERT INTO financeiro (valor, tipo_custo, data) VALUES (?,?,?)", (val, 'Combustível', data))
        conn.commit(); st.success("Registrado!")
    st.dataframe(pd.read_sql("SELECT * FROM financeiro", conn))

def mod_auditoria():
    st.header("📋 Auditoria Geral")
    st.dataframe(pd.read_sql("SELECT * FROM checklists", conn))
    st.dataframe(pd.read_sql("SELECT * FROM financeiro", conn))

# --- NAVEGAÇÃO ---
def main():
    st.sidebar.title("SGF-Pro V19")
    menu = st.sidebar.radio("Módulos", [
        "📊 Dashboard", "🚗 Veículos", "👤 Motoristas", 
        "📝 Checklist", "🛠️ O.S.", "⛽ Abastecimento", "📋 Auditoria"
    ])
    
    func = {
        "📊 Dashboard": mod_dashboard, "🚗 Veículos": mod_veiculos, 
        "👤 Motoristas": mod_motoristas, "📝 Checklist": mod_checklist, 
        "🛠️ O.S.": mod_os, "⛽ Abastecimento": mod_abastecimento, 
        "📋 Auditoria": mod_auditoria
    }
    func[menu]()

if __name__ == "__main__":
    main()
