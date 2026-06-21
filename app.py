import streamlit as st
import sqlite3
import pandas as pd
import io
from datetime import datetime

# 1. CONFIGURAÇÃO E BANCO
def get_conn():
    return sqlite3.connect("frota_elite.db", check_same_thread=False)

conn = get_conn()
conn.execute("""
    CREATE TABLE IF NOT EXISTS frota (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT, modelo TEXT, custo REAL, data_revisao TEXT, data_ipva TEXT
    )
""")
conn.commit()

st.set_page_config(page_title="SGF-Fleet Pro", layout="wide")
st.title("🚛 SGF-Fleet Pro: Gestão de Frotas")

tab1, tab2 = st.tabs(["➕ Cadastrar Veículo", "⚙️ Gerenciar e Exportar"])

# 2. ABA DE CADASTRO
with tab1:
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        custo = col3.number_input("Custo de Manutenção", min_value=0.0)
        
        col4, col5 = st.columns(2)
        data_revisao = col4.date_input("Próxima Revisão")
        data_ipva = col5.date_input("Vencimento IPVA")
        
        if st.form_submit_button("Salvar Veículo"):
            if placa:
                conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?,?,?,?,?)", 
                             (placa, modelo, custo, str(data_revisao), str(data_ipva)))
                conn.commit()
                st.success("Veículo salvo com sucesso!")
            else:
                st.error("A placa é obrigatória.")

# 3. ABA DE GERENCIAMENTO E EXPORTAÇÃO
with tab2:
    df = pd.read_sql("SELECT * FROM frota", conn)
    
    if not df.empty:
        # Edição e Exclusão
        with st.expander("Editar ou Excluir Veículo"):
            veiculo_id = st.selectbox("Selecione o ID do veículo para editar", df['id'].tolist())
            veiculo_sel = df[df['id'] == veiculo_id].iloc[0]
            
            with st.form("form_edicao"):
                n_placa = st.text_input("Placa", value=veiculo_sel['placa'])
                n_modelo = st.text_input("Modelo", value=veiculo_sel['modelo'])
                n_custo = st.number_input("Custo", value=float(veiculo_sel['custo']))
                n_revisao = st.date_input("Próxima Revisão", value=datetime.strptime(veiculo_sel['data_revisao'], '%Y-%m-%d'))
                n_ipva = st.date_input("Vencimento IPVA", value=datetime.strptime(veiculo_sel['data_ipva'], '%Y-%m-%d'))
                
                if st.form_submit_button("Salvar Alterações"):
                    conn.execute("UPDATE frota SET placa=?, modelo=?, custo=?, data_revisao=?, data_ipva=? WHERE id=?", 
                                 (n_placa.upper(), n_modelo, n_custo, str(n_revisao), str(n_ipva), veiculo_id))
                    conn.commit()
                    st.rerun()

            if st.button("🗑️ Excluir este registro permanentemente", type="primary"):
                conn.execute("DELETE FROM frota WHERE id = ?", (veiculo_id,))
                conn.commit()
                st.rerun()

        # Listagem com Filtro
        st.divider()
        st.subheader("Veículos Ativos e Prazos")
        
        df_display = df.copy()
        df_display['data_revisao'] = pd.to_datetime(df_display['data_revisao'])
        df_display['data_ipva'] = pd.to_datetime(df_display['data_ipva'])
        
        limite = datetime.now() + pd.Timedelta(days=30)
        mostrar_pendentes = st.toggle("Mostrar apenas vencimentos nos próximos 30 dias")
        
        if mostrar_pendentes:
            df_display = df_display[(df_display['data_revisao'] <= limite) | (df_display['data_ipva'] <= limite)]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Exportação Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Frota')
        
        st.download_button(
            label="📥 Exportar Relatório para Excel",
            data=buffer.getvalue(),
            file_name="relatorio_frota.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum veículo cadastrado no momento.")
