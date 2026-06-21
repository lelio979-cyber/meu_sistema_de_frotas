import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Conexão aprimorada
conn = sqlite3.connect("sgf_erp_pro.db", check_same_thread=False)

# Módulo de Sinistros Expandido
def modulo_sinistros():
    st.header("💥 Gestão Detalhada de Sinistros")
    
    with st.expander("➕ Registrar Novo Sinistro"):
        with st.form("form_sinistro_completo"):
            col1, col2 = st.columns(2)
            id_v = col1.number_input("ID Veículo", min_value=1)
            tipo_sinistro = col2.selectbox("Tipo de Ocorrência", ["Colisão", "Furto/Roubo", "Incêndio", "Desastre Natural"])
            
            data_ocorrencia = st.date_input("Data do Ocorrido")
            local = st.text_input("Endereço/Local do Sinistro")
            
            st.divider()
            st.subheader("Dados de Terceiros")
            nome_terceiro = st.text_input("Nome do Terceiro (se houver)")
            placa_terceiro = st.text_input("Placa do Veículo Terceiro")
            
            st.divider()
            avarias = st.multiselect("Checklist de Avarias", ["Lataria", "Motor", "Vidros", "Suspensão", "Eletrica"])
            detalhes = st.text_area("Descrição detalhada do ocorrido")
            
            if st.form_submit_button("Registrar Sinistro Completo"):
                # Salvando no banco
                conn.execute("""INSERT INTO sinistros 
                    (id_veiculo, tipo, data, local, terceiro, placa_terceiro, detalhes) 
                    VALUES (?,?,?,?,?,?,?)""", 
                    (id_v, tipo_sinistro, data_ocorrencia, local, nome_terceiro, placa_terceiro, detalhes))
                conn.commit()
                st.success("Sinistro registrado com nível de auditoria!")

    # Exibição analítica
    st.subheader("Histórico de Sinistros")
    df = pd.read_sql("SELECT * FROM sinistros", conn)
    st.dataframe(df, use_container_width=True)

# Chamada do menu
menu = st.sidebar.selectbox("Módulo", ["Dashboard", "Sinistros", "Manutenção"])
if menu == "Sinistros": modulo_sinistros()
