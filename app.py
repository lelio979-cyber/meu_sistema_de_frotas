import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px

# --- 1. CONFIGURAÇÃO E BANCO (V15) ---
st.set_page_config(page_title="SGF-Pro V15", layout="wide")
conn = sqlite3.connect('frotas_final.db', check_same_thread=False)

def init_db():
    conn.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, km_proxima_revisao INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS motoristas (nome TEXT PRIMARY KEY, cnh TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS checklists (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, km INTEGER, data TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS ordens_servico (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, descricao TEXT, status TEXT, custo REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, valor REAL, data TEXT, tipo_custo TEXT)")
    conn.commit()

init_db()

# --- 2. MÓDULOS ---
def modulo_veiculos():
    st.header("🚗 Gestão de Veículos")
    with st.form("veiculo"):
        p = st.text_input("Placa"); m = st.text_input("Modelo"); k = st.number_input("KM Atual", step=1)
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?)", (p, m, k, k+10000))
            conn.commit(); st.success("Veículo salvo!")

def modulo_motoristas():
    st.header("👤 Motoristas e Controle de KM")
    nome = st.text_input("Nome"); cnh = st.text_input("CNH")
    if st.button("Salvar Motorista"):
        conn.execute("INSERT OR REPLACE INTO motoristas VALUES (?,?)", (nome, cnh))
        conn.commit(); st.success("Motorista salvo!")
    st.table(pd.read_sql("SELECT * FROM motoristas", conn))

def modulo_checklist():
    st.header("📝 Checklist de Campo")
    # Lógica de inspeção rápida
    placa = st.selectbox("Placa", pd.read_sql("SELECT placa FROM veiculos", conn))
    if st.button("Finalizar Inspeção"):
        conn.execute("INSERT INTO checklists (placa, data) VALUES (?,?)", (placa, datetime.now()))
        conn.commit(); st.success("Checklist concluído.")

def modulo_os():
    st.header("🛠️ Ordens de Serviço e Manutenções")
    placa = st.selectbox("Veículo", pd.read_sql("SELECT placa FROM veiculos", conn))
    desc = st.text_area("Descrição do Serviço"); custo = st.number_input("Custo R$")
    if st.button("Abrir O.S."):
        conn.execute("INSERT INTO ordens_servico (placa, descricao, custo, status) VALUES (?,?,?,?)", (placa, desc, custo, 'Aberta'))
        conn.commit(); st.success("O.S. registrada.")

def modulo_abastecimento():
    st.header("⛽ Abastecimento e Auditoria")
    # Auditoria simples de custo
    valor = st.number_input("Valor R$")
    if st.button("Registrar Abastecimento"):
        conn.execute("INSERT INTO financeiro (valor, tipo_custo) VALUES (?,?)", (valor, 'Combustível'))
        conn.commit(); st.success("Registrado.")

def modulo_auditoria():
    st.header("📋 Auditoria de Checklists")
    df = pd.read_sql("SELECT * FROM checklists", conn)
    st.dataframe(df)

def modulo_usuarios():
    st.header("👥 Gerenciamento de Usuários")
    u = st.text_input("Usuário"); p = st.selectbox("Perfil", ["Gestor", "Operador"])
    if st.button("Criar Acesso"):
        conn.execute("INSERT INTO usuarios VALUES (?,?,?)", (u, 'hash', p))
        conn.commit(); st.success("Usuário criado.")

# --- 3. NAVEGAÇÃO FINAL ---
def main():
    menu = st.sidebar.radio("Navegação", [
        "🚗 Veículos", "👤 Motoristas", "📝 Checklist de Campo", 
        "🛠️ Ordens de Serviço", "⛽ Abastecimento", 
        "📋 Auditoria de Checklists", "👥 Gerenciamento de Usuários"
    ])
    
    if menu == "🚗 Veículos": modulo_veiculos()
    elif menu == "👤 Motoristas": modulo_motoristas()
    elif menu == "📝 Checklist de Campo": modulo_checklist()
    elif menu == "🛠️ Ordens de Serviço": modulo_os()
    elif menu == "⛽ Abastecimento": modulo_abastecimento()
    elif menu == "📋 Auditoria de Checklists": modulo_auditoria()
    elif menu == "👥 Gerenciamento de Usuários": modulo_usuarios()

main()
