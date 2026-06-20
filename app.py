import streamlit as st
import sqlite3
import pandas as pd

def get_db():
    return sqlite3.connect('frotas_limpo.db', check_same_thread=False)

def init_tables():
    conn = get_db()
    # Adicionando campos essenciais para uma gestão profissional
    conn.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY, 
            modelo TEXT,
            marca TEXT,
            ano INTEGER,
            chassi TEXT,
            renavam TEXT,
            data_aquisicao DATE,
            km_atual INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_tables()

def main():
    st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
    st.title("🚗 Cadastro Técnico de Frota")
    
    with st.form("form_veiculo_completo", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            placa = st.text_input("Placa").upper()
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
        with col2:
            ano = st.number_input("Ano Fabricação", 1990, 2030)
            chassi = st.text_input("Chassi")
            renavam = st.text_input("Renavam")
        with col3:
            data_aq = st.date_input("Data de Aquisição")
            km = st.number_input("KM Atual", min_value=0)
            status = st.selectbox("Status", ["Ativo", "Inativo", "Manutenção", "Vendido"])
        
        if st.form_submit_button("Salvar Veículo no Banco"):
            try:
                conn = get_db()
                conn.execute("""
                    INSERT INTO veiculos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (placa, modelo, marca, ano, chassi, renavam, data_aq, km, status))
                conn.commit()
                conn.close()
                st.success("Veículo cadastrado com especificações técnicas!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    # Exibição Técnica
    st.subheader("Frota Ativa")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()

if __name__ == "__main__":
    main()
