import streamlit as st
import sqlite3
import pandas as pd

# --- 1. PERSISTÊNCIA (Banco de Dados SQLite) ---
def init_db():
    conn = sqlite3.connect("frota_elite.db", check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS frota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT,
            modelo TEXT,
            custo REAL
        )
    """)
    conn.commit()
    return conn

conn = init_db()

st.set_page_config(layout="wide", page_title="Sistema de Frotas Elite")
st.title("🚛 Gestão de Frotas Elite")

# --- 2. OPERAÇÕES (Cadastro, Edição e Exclusão) ---
aba_cadastro, aba_relatorio = st.tabs(["Cadastro e Operações", "Relatórios Financeiros"])

with aba_cadastro:
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        custo = col3.number_input("Custo de Manutenção (R$)", min_value=0.0)
        
        if st.form_submit_button("Salvar Veículo"):
            conn.execute("INSERT INTO frota (placa, modelo, custo) VALUES (?, ?, ?)", (placa, modelo, custo))
            conn.commit()
            st.success("Veículo salvo com sucesso!")
            st.rerun()

    st.subheader("Veículos Ativos")
    df = pd.read_sql("SELECT * FROM frota", conn)
    
    # Exibição com botões de Ação
    for _, row in df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        c1.write(f"**{row['placa']}**")
        c2.write(f"{row['modelo']} - R$ {row['custo']:.2f}")
        if c3.button("Excluir", key=f"del_{row['id']}"):
            conn.execute("DELETE FROM frota WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()

# --- 3. RELATÓRIOS (Inteligência de Custos) ---
with aba_relatorio:
    st.subheader("Resumo Financeiro")
    df = pd.read_sql("SELECT * FROM frota", conn)
    if not df.empty:
        total = df['custo'].sum()
        st.metric("Custo Total da Frota", f"R$ {total:,.2f}")
        st.bar_chart(df.set_index('placa')['custo'])
    else:
        st.info("Nenhum custo registrado.")
