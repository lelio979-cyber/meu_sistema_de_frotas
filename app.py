import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# Configuração e Banco
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
conn = sqlite3.connect('frotas_pro.db', check_same_thread=False)

# --- MÓDULOS ---
def mod_dashboard():
    st.header("📊 Painel Estratégico (KPIs)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Custo Total", "R$ 28.400,00", "+5%")
    col2.metric("Veículos", "15", "0")
    col3.metric("Disponibilidade", "92%", "-1%")
    
    # Gráfico de Custos
    df = pd.read_sql("SELECT * FROM financeiro", conn)
    if not df.empty:
        fig = px.bar(df, x='data', y='valor', title="Tendência de Gastos")
        st.plotly_chart(fig, use_container_width=True)

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

def mod_os():
    st.header("🛠️ Ordens de Serviço")
    with st.form("os"):
        placa = st.text_input("Placa"); desc = st.text_area("Descrição"); cust = st.number_input("Custo")
        if st.form_submit_button("Abrir OS"):
            conn.execute("INSERT INTO ordens_servico (placa, descricao, custo, status) VALUES (?,?,?,?)", (placa, desc, cust, 'Aberta'))
            conn.commit(); st.success("OS Aberta!")

def mod_abastecimento():
    st.header("⛽ Abastecimento")
    val = st.number_input("Valor"); data = st.date_input("Data")
    if st.button("Registrar"):
        conn.execute("INSERT INTO financeiro (valor, tipo_custo, data) VALUES (?,?,?)", (val, 'Combustível', data))
        conn.commit(); st.success("Registrado!")

def mod_auditoria():
    st.header("📋 Auditoria Geral")
    st.write("Registros de Checklists:")
    st.dataframe(pd.read_sql("SELECT * FROM checklists", conn))
    st.write("Registros de Custos:")
    st.dataframe(pd.read_sql("SELECT * FROM financeiro", conn))

# --- NAVEGAÇÃO ---
def main():
    st.sidebar.title("SGF-Pro V17")
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
