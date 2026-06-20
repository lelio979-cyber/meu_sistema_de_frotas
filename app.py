import streamlit as st
import sqlite3
import pandas as pd

# --- CONEXÃO E ESTRUTURA ---
def init_db():
    conn = sqlite3.connect("frota_elite.db", check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, modelo TEXT, custo REAL)")
    conn.commit()
    return conn

conn = init_db()

st.set_page_config(layout="wide", page_title="SGF-Fleet Elite")
st.title("🚛 Gestão de Frotas Elite")

aba_cadastro, aba_relatorio = st.tabs(["Cadastro e Operações", "Relatórios e Exportação"])

with aba_cadastro:
    # Cadastro
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        custo = col3.number_input("Custo de Manutenção (R$)", min_value=0.0)
        
        if st.form_submit_button("Salvar Veículo"):
            conn.execute("INSERT INTO frota (placa, modelo, custo) VALUES (?, ?, ?)", (placa, modelo, custo))
            conn.commit()
            st.rerun()

    # --- FILTRO DE BUSCA ---
    st.subheader("Veículos Ativos")
    busca = st.text_input("🔍 Buscar por Placa:")
    query = "SELECT * FROM frota WHERE placa LIKE ?" if busca else "SELECT * FROM frota"
    params = (f"%{busca}%",) if busca else ()
    
    df = pd.read_sql(query, conn, params=params)
    
    for _, row in df.iterrows():
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{row['placa']}** - {row['modelo']} | R$ {row['custo']:.2f}")
        if c3.button("Excluir", key=f"del_{row['id']}"):
            conn.execute("DELETE FROM frota WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()

with aba_relatorio:
    st.subheader("Relatórios Financeiros")
    df_full = pd.read_sql("SELECT * FROM frota", conn)
    
    if not df_full.empty:
        st.metric("Total de Custos", f"R$ {df_full['custo'].sum():,.2f}")
        st.bar_chart(df_full.set_index('placa')['custo'])
        
        # --- EXPORTAÇÃO PARA CSV ---
        csv = df_full.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório em CSV",
            data=csv,
            file_name='relatorio_frota.csv',
            mime='text/csv',
        )
    else:
        st.info("Nenhum dado para exportar.")
