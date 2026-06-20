import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONEXÃO E ESTRUTURA ATUALIZADA ---
def init_db():
    conn = sqlite3.connect("frota_elite.db", check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS frota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT,
            modelo TEXT,
            custo REAL,
            data_revisao DATE,
            data_ipva DATE
        )
    """)
    conn.commit()
    return conn

conn = init_db()

st.set_page_config(layout="wide", page_title="SGF-Fleet Elite Pro")
st.title("🚛 Gestão de Frotas: Controle de Prazos")

aba1, aba2 = st.tabs(["Cadastro e Prazos", "Relatórios e Exportação"])

with aba1:
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        custo = col3.number_input("Custo de Manutenção (R$)", min_value=0.0)
        
        col4, col5 = st.columns(2)
        data_revisao = col4.date_input("Próxima Revisão")
        data_ipva = col5.date_input("Vencimento IPVA")
        
        if st.form_submit_button("Salvar Veículo"):
            conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?, ?, ?, ?, ?)", 
                         (placa, modelo, custo, str(data_revisao), str(data_ipva)))
            conn.commit()
            st.rerun()

    # --- LISTAGEM COM ALERTAS DE PRAZO ---
    st.subheader("Veículos Ativos")
    df = pd.read_sql("SELECT * FROM frota", conn)
    
    for _, row in df.iterrows():
        c1, c2, c3 = st.columns([3, 2, 1])
        rev_formatada = pd.to_datetime(row['data_revisao']).strftime('%d/%m/%Y')
        ipva_formatada = pd.to_datetime(row['data_ipva']).strftime('%d/%m/%Y')
        c1.write(f"🚗 **{row['placa']}** | 🛠️ Rev: {rev_formatada} | 📄 IPVA: {ipva_formatada}")
        
        # Alerta de Revisão
        if datetime.strptime(row['data_revisao'], '%Y-%m-%d') < datetime.now():
            c2.error("⚠️ Revisão Atrasada!")
            
        # Botão de Excluir
        if c3.button("Excluir", key=f"del_{row['id']}"):
            conn.execute("DELETE FROM frota WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()

with aba2:
    st.subheader("Relatórios Financeiros")
    df_full = pd.read_sql("SELECT * FROM frota", conn)
    
    if not df_full.empty:
        st.metric("Total de Custos", f"R$ {df_full['custo'].sum():,.2f}")
        csv = df_full.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Relatório Completo", csv, 'relatorio_frota.csv', 'text/csv')
    else:
        st.info("Nenhum dado cadastrado.")
