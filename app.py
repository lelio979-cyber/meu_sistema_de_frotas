import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Elite", layout="wide")

def get_db(): return sqlite3.connect("sgf_fleet_elite.db")

def setup_db():
    conn = get_db()
    # Tabelas principais
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS motoristas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cnh TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista_id INTEGER, codigo TEXT, valor REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, acao TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

setup_db()

# --- AUTENTICAÇÃO ---
if "user" not in st.session_state: st.session_state.user = {"login": "admin", "perm": "admin"}

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro Veículos", "Motoristas", "Multas"])

if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    col1, col2 = st.columns(2)
    col1.metric("Veículos Cadastrados", len(pd.read_sql("SELECT * FROM veiculos", get_db())))
    col2.metric("Motoristas Ativos", len(pd.read_sql("SELECT * FROM motoristas", get_db())))

elif menu == "Cadastro Veículos":
    st.title("📝 Cadastro de Veículos")
    with st.form("cad_veic"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        if st.form_submit_button("Salvar"):
            get_db().execute("INSERT OR REPLACE INTO veiculos VALUES (?,?)", (placa, modelo))
            st.success("Veículo salvo!")

elif menu == "Motoristas":
    st.title("👤 Cadastro de Motoristas")
    with st.form("cad_mot"):
        nome = st.text_input("Nome do Motorista")
        cnh = st.text_input("Número da CNH")
        if st.form_submit_button("Cadastrar Motorista"):
            get_db().execute("INSERT INTO motoristas (nome, cnh) VALUES (?,?)", (nome, cnh))
            st.success("Motorista cadastrado!")

elif menu == "Multas":
    st.title("🚦 Módulo de Multas")
    
    # Base de referência (Pode ser expandida ou movida para um JSON externo)
    ctb_ref = {"50100": 130.16, "50291": 293.47, "74550": 130.16}
    
    conn = get_db()
    placas = pd.read_sql("SELECT placa FROM veiculos", conn)['placa'].tolist()
    motoristas = pd.read_sql("SELECT id, nome FROM motoristas", conn)
    conn.close()
    
    with st.form("form_multa"):
        placa = st.selectbox("Veículo", placas)
        motorista_id = st.selectbox("Motorista", motoristas['nome'])
        codigo = st.text_input("Código da Infração (Ex: 50100)")
        
        if st.form_submit_button("Registrar Multa"):
            valor = ctb_ref.get(codigo, 0.0)
            if valor > 0:
                conn = get_db()
                conn.execute("INSERT INTO multas (placa, motorista_id, codigo, valor) VALUES (?,?,?,?)", 
                             (placa, motorista_id, codigo, valor))
                conn.commit()
                conn.close()
                st.success(f"Multa registrada com sucesso. Valor: R$ {valor}")
            else:
                st.error("Código de infração inválido.")
