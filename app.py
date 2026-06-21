import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO E LOGIN SIMPLES ---
st.set_page_config(page_title="SGF-Fleet Pro Elite", layout="wide")

def check_password():
    if "logged_in" not in st.session_state:
        st.sidebar.title("🔐 Acesso Restrito")
        password = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            if password == "admin123": # Altere a senha aqui
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Senha incorreta")
        return False
    return True

if not check_password():
    st.stop()

# --- BANCO DE DADOS (Estrutura Completa) ---
conn = sqlite3.connect("frota_elite.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY, placa TEXT, modelo TEXT, custo REAL, data_revisao TEXT, data_ipva TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, acao TEXT, data TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, id_veiculo INTEGER, descricao TEXT, valor REAL, data TEXT)")
conn.commit()

# --- DASHBOARD VISUAL ---
st.title("🚛 SGF-Fleet Pro Elite")
df = pd.read_sql("SELECT * FROM frota", conn)

if not df.empty:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Total de Veículos", len(df))
        st.metric("Custo Total da Frota", f"R$ {df['custo'].sum():,.2f}")
    with col2:
        fig = px.bar(df, x='modelo', y='custo', title="Custo por Modelo")
        st.plotly_chart(fig, use_container_width=True)

# --- TABELA COLORIDA (Estilização) ---
def highlight_status(row):
    hoje = pd.Timestamp.now()
    rev = pd.to_datetime(row['data_revisao'])
    color = ''
    if rev < hoje: color = 'background-color: #ffcccc' # Vermelho
    elif (rev - hoje).days < 7: color = 'background-color: #fff3cd' # Amarelo
    return [color] * len(row)

st.subheader("Estado da Frota")
if not df.empty:
    # Aplicando estilo na tabela
    df_styled = df.style.apply(highlight_status, axis=1)
    st.dataframe(df_styled, use_container_width=True)

# --- LOG DE AÇÕES ---
def registrar_log(acao):
    conn.execute("INSERT INTO logs (acao, data) VALUES (?, ?)", (acao, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

# --- FUNCIONALIDADES (Resumo da interface) ---
tab1, tab2 = st.tabs(["➕ Adicionar Veículo", "📜 Histórico de Ações"])
with tab1:
    with st.form("cadastro"):
        # ... (Inputs do formulário anterior)
        if st.form_submit_button("Salvar"):
            # ... (código de insert)
            registrar_log(f"Veículo cadastrado")
            st.success("Salvo!")

with tab2:
    st.write(pd.read_sql("SELECT * FROM logs ORDER BY id DESC LIMIT 10", conn))
