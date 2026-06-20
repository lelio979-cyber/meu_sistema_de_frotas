import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Elite Pro", layout="wide")
DB_NAME = "sgf_fleet_elite.db"

# --- INICIALIZAÇÃO DE BANCO ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Estruturas de Dados
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, km_atual INTEGER, km_revisao INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, data DATE)")
    conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, valor REAL, comprovante_link TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS abastecimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, litros REAL, km_percorrido REAL)")
    conn.commit(); conn.close()

init_db()

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Painel de Performance (Elite Pro)")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    if not df_v.empty:
        for _, veic in df_v.iterrows():
            total_custo = df_os[df_os['placa'] == veic['placa']]['custo'].sum()
            with st.expander(f"🚛 {veic['placa']} | {veic['modelo']}"):
                c1, c2 = st.columns(2)
                c1.metric("KM Atual", f"{veic['km_atual']:,}")
                c2.metric("Custo Manutenção", f"R$ {total_custo:,.2f}")
    else:
        st.info("Nenhum veículo cadastrado.")

def gestao_frota():
    st.title("🚛 Cadastro de Ativos")
    with st.form("form_veic", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        motorista = col1.text_input("Motorista")
        km = col2.number_input("KM Atual", min_value=0)
        km_rev = col1.number_input("KM Próxima Revisão", min_value=0)
        if st.form_submit_button("Registrar"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?)", (placa, modelo, motorista, km, km_rev))
            conn.commit(); conn.close(); st.success("Ativo registrado!"); st.rerun()

def gestao_multas():
    st.title("⚠️ Registro de Multas")
    with st.form("form_multa"):
        placa = st.text_input("Placa").upper()
        motorista = st.text_input("Motorista")
        valor = st.number_input("Valor da Multa (R$)", min_value=0.0)
        link = st.text_input("Link da Foto do Comprovante")
        if st.form_submit_button("Registrar Multa"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO multas (placa, motorista, valor, comprovante_link) VALUES (?,?,?,?)", (placa, motorista, valor, link))
            conn.commit(); conn.close(); st.success("Multa salva!"); st.rerun()

def controle_combustivel():
    st.title("⛽ Controle de Consumo (KM/L)")
    with st.form("form_combustivel"):
        placa = st.text_input("Placa").upper()
        litros = st.number_input("Litros Abastecidos", min_value=0.1)
        km_rodado = st.number_input("KM Percorrido", min_value=0.1)
        if st.form_submit_button("Calcular Média"):
            media = km_rodado / litros
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO abastecimentos (placa, litros, km_percorrido) VALUES (?,?,?)", (placa, litros, km_rodado))
            conn.commit(); conn.close()
            st.success(f"Média: {media:.2f} KM/L salva!")

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Ativos", "Lançar OS", "Apontar KM", "Multas", "Combustível", "Relatório"])

if menu == "Dashboard": dashboard()
elif menu == "Gestão de Ativos": gestao_frota()
elif menu == "Multas": gestao_multas()
elif menu == "Combustível": controle_combustivel()
# (Adicione as chamadas de lancar_os, apontar_km e exportar_relatorio aqui conforme necessário)
