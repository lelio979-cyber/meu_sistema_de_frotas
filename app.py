import streamlit as st
import sqlite3
import pandas as pd

# Conecta ao banco
conn = sqlite3.connect("frota_elite.db", check_same_thread=False)

# Adiciona as colunas com segurança (IF NOT EXISTS)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE frota ADD COLUMN data_revisao TEXT")
    cursor.execute("ALTER TABLE frota ADD COLUMN data_ipva TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass # Colunas já existem, tudo bem!

st.title("🚛 Gestão de Frotas: Controle de Prazos")

# Formulário atualizado
with st.form("form", clear_on_submit=True):
    placa = st.text_input("Placa").upper()
    modelo = st.text_input("Modelo")
    custo = st.number_input("Custo", min_value=0.0)
    data_revisao = st.date_input("Próxima Revisão")
    data_ipva = st.date_input("Vencimento IPVA")
    
    if st.form_submit_button("Salvar"):
        conn.execute("INSERT INTO frota (placa, modelo, custo, data_revisao, data_ipva) VALUES (?, ?, ?, ?, ?)", 
                     (placa, modelo, custo, str(data_revisao), str(data_ipva)))
        conn.commit()
        st.rerun()

# --- EXIBIÇÃO COM ALERTAS ---
st.subheader("Veículos Ativos")
df = pd.read_sql("SELECT * FROM frota", conn)

if not df.empty:
    # Função para verificar o status
    def verificar_status(data_str):
        if not data_str or data_str == "None":
            return "Indefinido"
        # Compara a data do banco com a data de hoje (20/06/2026)
        if data_str < "2026-06-20":
            return "⚠️ Atrasado"
        return "✅ Em dia"

    # Aplica a lógica de status nas colunas
    df['Status Revisão'] = df['data_revisao'].apply(verificar_status)
    df['Status IPVA'] = df['data_ipva'].apply(verificar_status)

    # Exibe a tabela com os status
    st.dataframe(
        df, 
        column_config={
            "status": st.column_config.TextColumn("Status"),
        },
        use_container_width=True
    )

    # Filtro opcional: Mostrar apenas alertas
    if st.checkbox("Mostrar apenas veículos com alertas"):
        alertas = df[(df['Status Revisão'] == "⚠️ Atrasado") | (df['Status IPVA'] == "⚠️ Atrasado")]
        st.warning("Veículos que precisam de atenção imediata:")
        st.table(alertas)
else:
    st.info("Nenhum veículo cadastrado.")
