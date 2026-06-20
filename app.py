import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SGF-Pro V30", layout="wide")

def get_conn():
    return sqlite3.connect('frotas_v30.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, marca TEXT, 
        km_inicio INTEGER, km_atual INTEGER, status TEXT, 
        data_inicio DATE, data_fim DATE, doc_path TEXT)""")
    conn.commit()
    conn.close()

init_db()

# --- MÓDULO DE DASHBOARD COM ALERTAS ---
def exibir_dashboard():
    st.title("📊 Painel Executivo de Frota")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df.empty:
        # Lógica de Alerta: Veículos com vigência próxima ao fim (próximos 30 dias)
        hoje = datetime.now().date()
        df['data_fim'] = pd.to_datetime(df['data_fim']).dt.date
        alertas = df[df['data_fim'] <= (hoje + pd.Timedelta(days=30))]
        
        if not alertas.empty:
            st.error(f"⚠️ ATENÇÃO: {len(alertas)} veículo(s) com contrato próximo ao vencimento!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Frota Ativa", len(df))
        c2.metric("KM Média", f"{df['km_atual'].mean():.0f}")
        c3.metric("Contratos Vencendo", len(alertas))
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum ativo cadastrado.")

# --- CADASTRO ROBUSTO DE VIGÊNCIA ---
def exibir_cadastro():
    st.title("➕ Cadastro e Vigência de Ativo")
    with st.form("form_v30"):
        col1, col2 = st.columns(2)
        with col1:
            placa = st.text_input("Placa").upper()
            km_in = st.number_input("KM na Entrada", 0)
            data_ini = st.date_input("Início da Vigência")
        with col2:
            data_fim = st.date_input("Fim da Vigência")
            doc = st.file_uploader("Upload Documento (PDF)", type=['pdf'])
            status = st.selectbox("Status", ["Ativo", "Manutenção", "Vencido"])
            
        if st.form_submit_button("Salvar Ativo"):
            conn = get_conn()
            # O documento será tratado como string do nome para simplificar
            conn.execute("INSERT OR REPLACE INTO veiculos (placa, km_inicio, km_atual, data_inicio, data_fim, status, doc_path) VALUES (?,?,?,?,?,?,?)",
                         (placa, km_in, km_in, data_ini, data_fim, status, str(doc.name) if doc else None))
            conn.commit()
            conn.close()
            st.success("Ativo registrado com ciclo de vigência definido!")

# --- FLUXO PRINCIPAL ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    # [Lógica de Login mantida...]
    pass
else:
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])
    if menu == "Dashboard": exibir_dashboard()
    else: exibir_cadastro()
