import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
DB_NAME = "sgf_final.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    # Cria tabelas se não existirem
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        data_devolucao DATE, valor_locacao REAL, usuario TEXT, 
        cidade TEXT, doc_path TEXT)""")
    
    # --- CHECK DE SEGURANÇA: Adiciona colunas se faltarem ---
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    cols = [info[1] for info in cursor.fetchall()]
    
    colunas_necessarias = {
        'marca': 'TEXT', 'modelo': 'TEXT', 'status': 'TEXT', 
        'combustivel': 'TEXT', 'km_inicial': 'INTEGER', 'data_aquisicao': 'DATE',
        'data_devolucao': 'DATE', 'valor_locacao': 'REAL', 'usuario': 'TEXT',
        'cidade': 'TEXT', 'doc_path': 'TEXT'
    }
    
    for col, tipo in colunas_necessarias.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE veiculos ADD COLUMN {col} {tipo}")
            
    conn.commit()
    conn.close()
init_db()

# --- LÓGICA DE LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.title("🔐 Login SGF-Pro")
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = get_conn()
        perfil = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        conn.close()
        if perfil:
            st.session_state['logado'] = True; st.session_state['perfil'] = perfil[0]; st.rerun()
    st.stop()

# --- MODULOS ---
def exibir_dashboard():
    st.title("📊 Dashboard Executivo - Gestão de Frota")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_d = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    
    if not df_v.empty:
        # Layout de métricas superiores (Simulando a imagem)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Frota Ativa", len(df_v[df_v['status']=='Ativo']))
        col2.metric("Custo Mensal", f"R$ {df_d['valor'].sum():,.2f}")
        col3.metric("KM Média", f"{df_v['km_inicial'].mean():.0f}")
        col4.metric("Alertas", 0)
        
        st.divider()
        # Gráficos de análise
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição de Status")
            fig = px.pie(df_v, names='status', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Veículos por Cidade")
            st.bar_chart(df_v['cidade'].value_counts())
    else: st.info("Nenhum veículo cadastrado.")

def exibir_cadastro():
    st.title("➕ Cadastro Detalhado de Veículo")
    with st.form("form_completo"):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        marca = c2.text_input("Marca")
        modelo = c1.text_input("Modelo")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        comb = c1.selectbox("Tipo de Combustível", ["Gasolina", "Etanol", "Diesel S10", "Flex"])
        km = c2.number_input("KM Inicial", 0)
        dt_aq = c1.date_input("Data de Aquisição")
        dt_dev = c2.date_input("Data de Devolução")
        valor = c1.number_input("Valor de Locação (R$)", 0.0)
        user = c2.text_input("Quem utiliza")
        cidade = c1.text_input("Cidade")
        doc = c2.file_uploader("Documento do Veículo")
        
        if st.form_submit_button("Salvar Veículo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (placa, marca, modelo, status, comb, km, dt_aq, dt_dev, valor, user, cidade, str(doc.name) if doc else None))
            conn.commit()
            conn.close()
            st.success("Veículo salvo com sucesso!")

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro Veículo", "Lançar Custo"])
if menu == "Dashboard": exibir_dashboard()
elif menu == "Cadastro Veículo": exibir_cadastro()
else: st.write("Módulo de Custos...")

st.sidebar.button("Sair", on_click=lambda: st.session_state.update({'logado': False}))
