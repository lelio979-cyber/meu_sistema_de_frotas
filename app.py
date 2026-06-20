import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SGF-Pro V32", layout="wide")

def get_conn():
    return sqlite3.connect('frotas_v32.db', check_same_thread=False)

def init_db():
    conn = get_conn()
    # Estrutura robusta com campos de gestão
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, marca TEXT, chassi TEXT, renavam TEXT,
        ano INTEGER, km_inicial INTEGER, km_atual INTEGER, valor_compra REAL,
        status TEXT, data_aquisicao DATE, data_inicio DATE, data_fim DATE, doc_path TEXT)""")
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, perfil TEXT)")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- DASHBOARD ROBUSTO ---
def exibir_dashboard():
    st.title("📊 Painel de Controle de Frota")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()
    
    if not df.empty:
        # KPIs de Gestão
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Valor Total Frota", f"R$ {df['valor_compra'].sum():,.2f}")
        c2.metric("Frota Ativa", len(df[df['status'] == 'Ativo']))
        c3.metric("KM Média", f"{df['km_atual'].mean():.0f} km")
        c4.metric("Vencendo em 30 dias", len(df[pd.to_datetime(df['data_fim']).dt.date <= (datetime.now().date() + pd.Timedelta(days=30))]))
        
        st.subheader("Análise Detalhada")
        st.dataframe(df.style.format({"valor_compra": "R$ {:.2f}"}), use_container_width=True)
    else:
        st.info("Nenhum ativo registrado.")

# --- CADASTRO TÉCNICO ---
def exibir_cadastro():
    st.title("➕ Cadastro Técnico de Ativo")
    with st.form("form_completo"):
        c1, c2, c3 = st.columns(3)
        with c1:
            placa = st.text_input("Placa").upper()
            modelo = st.text_input("Modelo")
            marca = st.text_input("Marca")
            chassi = st.text_input("Chassi")
        with c2:
            renavam = st.text_input("Renavam")
            ano = st.number_input("Ano Fabricação", 1990, 2030)
            km = st.number_input("KM Inicial", 0)
            valor = st.number_input("Valor de Aquisição (R$)", 0.0)
        with c3:
            data_aq = st.date_input("Data de Aquisição")
            data_ini = st.date_input("Início da Vigência")
            data_fim = st.date_input("Fim da Vigência")
            status = st.selectbox("Status", ["Ativo", "Manutenção", "Vencido", "Baixado"])
            doc = st.file_uploader("Documento PDF")

        if st.form_submit_button("Salvar Registro Completo"):
            conn = get_conn()
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (placa, modelo, marca, chassi, renavam, ano, km, km, valor, status, data_aq, data_ini, data_fim, str(doc.name) if doc else None))
            conn.commit()
            conn.close()
            st.success(f"Ativo {placa} registrado com sucesso!")

# [Lógica de Login e Navegação mantida...]
