import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Pro ERP", layout="wide")
conn = sqlite3.connect("sgf_erp_pro.db", check_same_thread=False)
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

# --- DICIONÁRIO DE MULTAS ---
DICIONARIO_MULTAS = {
    "501-1": {"desc": "Excesso de velocidade > 50%", "valor": 880.41, "pontos": 7, "gravidade": "Gravíssima"},
    "602-0": {"desc": "Conduzir sem cinto", "valor": 195.23, "pontos": 5, "gravidade": "Grave"},
    "518-5": {"desc": "Estacionar em local proibido", "valor": 130.16, "pontos": 4, "gravidade": "Média"}
}

# --- TABELAS ---
conn.execute("CREATE TABLE IF NOT EXISTS frota (id INTEGER PRIMARY KEY, placa TEXT, modelo TEXT, status TEXT DEFAULT 'Disponível')")
conn.execute("CREATE TABLE IF NOT EXISTS abastecimento (id INTEGER PRIMARY KEY, id_veiculo INTEGER, km REAL, litros REAL, valor REAL, data TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY, id_veiculo INTEGER, desc TEXT, custo REAL, data TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY, id_veiculo INTEGER, codigo TEXT, local TEXT, data TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS sinistros (id INTEGER PRIMARY KEY, id_veiculo INTEGER, local TEXT, detalhes TEXT, foto_path TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS aprovacoes (id INTEGER PRIMARY KEY, ref_id INTEGER, tipo TEXT, aprovador TEXT, data TEXT)")
conn.commit()

# --- FUNÇÕES AUXILIARES ---
def update_status(id_v, status):
    conn.execute("UPDATE frota SET status = ? WHERE id = ?", (status, id_v))
    conn.commit()

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro Veículos", "Abastecimento", "Manutenção (OS)", "Multas", "Sinistros", "Aprovações", "Consultas Dinâmicas"])

# --- LÓGICA DOS MÓDULOS ---
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    df = pd.read_sql("SELECT status, count(*) as total FROM frota GROUP BY status", conn)
    st.plotly_chart(px.pie(df, values='total', names='status', title="Status Atual da Frota"), use_container_width=True)

elif menu == "Cadastro Veículos":
    with st.form("cad_veiculo"):
        p, m = st.text_input("Placa"), st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT INTO frota (placa, modelo) VALUES (?,?)", (p, m))
            conn.commit()
            st.success("Veículo cadastrado!")

elif menu == "Manutenção (OS)":
    with st.form("os"):
        id_v = st.number_input("ID Veículo", 1)
        desc = st.text_area("Descrição")
        custo = st.number_input("Custo")
        if st.form_submit_button("Abrir OS"):
            conn.execute("INSERT INTO manutencao (id_veiculo, desc, custo, data) VALUES (?,?,?,?)", (id_v, desc, custo, datetime.now().strftime("%Y-%m-%d")))
            update_status(id_v, "Em Manutenção")
            conn.commit()
            st.success("OS Aberta e Status alterado!")

elif menu == "Multas":
    cod = st.selectbox("Código", list(DICIONARIO_MULTAS.keys()))
    info = DICIONARIO_MULTAS[cod]
    st.info(f"Gravidade: {info['gravidade']} | Valor: R$ {info['valor']}")
    id_v = st.number_input("ID Veículo")
    if st.button("Lançar Multa"):
        conn.execute("INSERT INTO multas (id_veiculo, codigo, data) VALUES (?,?,?)", (id_v, cod, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        st.success("Multa registrada!")

elif menu == "Sinistros":
    with st.form("sinistro"):
        id_v = st.number_input("ID Veículo")
        det = st.text_area("Detalhes")
        foto = st.file_uploader("Foto", type=['jpg', 'png'])
        if st.form_submit_button("Salvar"):
            path = ""
            if foto:
                path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}.jpg")
                with open(path, "wb") as f: f.write(foto.getbuffer())
            conn.execute("INSERT INTO sinistros (id_veiculo, detalhes, foto_path) VALUES (?,?,?)", (id_v, det, path))
            update_status(id_v, "Sinistrado")
            conn.commit()
            st.success("Sinistro salvo!")

elif menu == "Aprovações":
    with st.form("aprov"):
        ref = st.number_input("ID da Referência (OS ou Checklist)")
        tipo = st.selectbox("Tipo", ["OS", "Checklist"])
        aprov = st.text_input("Aprovador")
        if st.form_submit_button("Aprovar"):
            conn.execute("INSERT INTO aprovacoes (ref_id, tipo, aprovador, data) VALUES (?,?,?,?)", (ref, tipo, aprov, datetime.now().strftime("%Y-%m-%d")))
            update_status(ref, "Disponível")
            conn.commit()
            st.success("Aprovado! Status liberado.")

elif menu == "Consultas Dinâmicas":
    tabela = st.selectbox("Tabela", ["frota", "manutencao", "multas", "sinistros"])
    df = pd.read_sql(f"SELECT * FROM {tabela}", conn)
    st.dataframe(df, use_container_width=True)
