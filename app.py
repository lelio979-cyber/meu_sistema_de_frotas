import streamlit as st
import sqlite3
import pandas as pd

# --- 1. PERSISTÊNCIA (Banco de Dados) ---
conn = sqlite3.connect("sgf_frota.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, modelo TEXT, custo_manutencao REAL)")
conn.commit()

st.title("🚛 SGF-Fleet Pro: Gestão Profissional")

# --- 2. OPERAÇÕES (Cadastro, Edição e Exclusão) ---
aba1, aba2 = st.tabs(["Cadastro e Gestão", "Relatório de Custos"])

with aba1:
    with st.form("cadastro"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        custo = st.number_input("Custo de Manutenção Inicial (R$)", min_value=0.0)
        if st.form_submit_button("Salvar Veículo"):
            conn.execute("INSERT INTO frota (placa, modelo, custo_manutencao) VALUES (?,?,?)", (placa, modelo, custo))
            conn.commit()
            st.success("Veículo salvo!")
            st.rerun()

    # Exibe a lista para Edição/Exclusão
    df = pd.read_sql("SELECT * FROM frota", conn)
    st.subheader("Veículos Cadastrados")
    
    for index, row in df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.write(f"{row['placa']} - {row['modelo']}")
        col2.write(f"R$ {row['custo_manutencao']:.2f}")
        if col3.button("Excluir", key=f"del_{row['id']}"):
            conn.execute("DELETE FROM frota WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()

# --- 3. RELATÓRIOS (Inteligência de Custos) ---
with aba2:
    st.subheader("Resumo Financeiro da Frota")
    if not df.empty:
        total = df['custo_manutencao'].sum()
        st.metric("Custo Total Acumulado", f"R$ {total:,.2f}")
        st.bar_chart(df.set_index('placa')['custo_manutencao'])
    else:
        st.info("Nenhum custo registrado.")
