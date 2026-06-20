import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "frota_base.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Criamos a tabela base
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    
    # Verificamos se a coluna 'km_atual' já existe, se não, adicionamos
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'km_atual' not in columns:
        conn.execute("ALTER TABLE veiculos ADD COLUMN km_atual INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

init_db()

st.title("SGF-Fleet: Módulo de Cadastro (Atualizado)")

with st.form("form_cadastro"):
    col1, col2 = st.columns(2)
    placa = col1.text_input("Placa").upper()
    modelo = col1.text_input("Modelo")
    km = col2.number_input("KM Atual", min_value=0, step=1)
    btn_salvar = st.form_submit_button("Salvar Veículo")

    if btn_salvar:
        if placa and modelo:
            conn = sqlite3.connect(DB_NAME)
            try:
                # O comando REPLACE permite atualizar a linha se a placa já existir
                conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, km_atual) VALUES (?, ?, ?)", 
                             (placa, modelo, km))
                conn.commit()
                st.success(f"Veículo {placa} salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                conn.close()
        else:
            st.warning("Preencha Placa e Modelo.")

st.divider()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM veiculos", conn)
conn.close()
st.dataframe(df, use_container_width=True)
