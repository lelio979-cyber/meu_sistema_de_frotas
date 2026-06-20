import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Professional", layout="wide")
DB_NAME = "sgf_fleet.db"

# --- INICIALIZAÇÃO SEGURA ---
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, motorista TEXT, status TEXT, km_atual INTEGER)")
        conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, data DATE)")
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro na inicialização do banco: {e}")

init_db()

# --- MÓDULOS ---
def dashboard():
    st.title("📊 Painel de Controle Corporativo")
    conn = sqlite3.connect(DB_NAME)
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    st.subheader("Frota Ativa e Prontuários")
    
    if not df_v.empty:
        # Loop para criar um "Prontuário" expansível para cada veículo
        for _, veic in df_v.iterrows():
            with st.expander(f"🚛 Placa: {veic['placa']} | Modelo: {veic['modelo']} | Status: {veic['status']}"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**Motorista:** {veic['motorista']}")
                col_a.write(f"**KM Atual:** {veic['km_atual']}")
                
                # Filtrar OS específicas desta placa
                historico = df_os[df_os['placa'] == veic['placa']]
                
                if not historico.empty:
                    col_b.write("**Histórico de Manutenções:**")
                    col_b.dataframe(historico[['data', 'servico', 'custo']], use_container_width=True)
                    st.write(f"**Custo Acumulado:** R$ {historico['custo'].sum():,.2f}")
                else:
                    col_b.info("Nenhuma manutenção registrada para este veículo.")
    else:
        st.info("Nenhum veículo cadastrado.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

def gestao_frota():
    st.title("🚛 Gestão de Ativos")
    with st.form("form_veic"):
        col1, col2 = st.columns(2)
        placa = col1.text_input("Placa").upper()
        modelo = col2.text_input("Modelo")
        motorista = col1.text_input("Motorista")
        status = col2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        km = col1.number_input("KM Atual", min_value=0)
        
        if st.form_submit_button("Salvar Veículo"):
            try:
                conn = sqlite3.connect(DB_NAME)
                # Incluímos 'None' para a 6ª coluna (crlv_path ou vencimento) que o banco exige
                conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?)", 
                             (placa, modelo, motorista, status, km, None))
                conn.commit(); conn.close()
                st.success("Veículo atualizado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

def abrir_os():
    st.title("🛠️ Lançar OS")
    conn = sqlite3.connect(DB_NAME)
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)['placa'].tolist()
    conn.close()
    
    if not veiculos:
        st.warning("Cadastre um veículo antes de abrir uma OS.")
        return

    with st.form("form_os"):
        placa = st.selectbox("Selecione o Veículo", veiculos)
        servico = st.text_input("Serviço")
        custo = st.number_input("Custo (R$)", min_value=0.0)
        data = st.date_input("Data")
        
        if st.form_submit_button("Lançar OS"):
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO os (placa, servico, custo, data) VALUES (?,?,?,?)", 
                             (placa, servico, custo, data))
                conn.commit(); conn.close()
                st.success("OS lançada!")
            except Exception as e:
                st.error(f"Erro ao salvar OS: {e}")

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota", "Lançar OS"])
if menu == "Dashboard": dashboard()
elif menu == "Gestão de Frota": gestao_frota()
elif menu == "Lançar OS": abrir_os()
