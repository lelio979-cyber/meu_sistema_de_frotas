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
    # Adicionando a coluna crlv_path caso não exista
    conn.execute("""CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, status TEXT, 
        combustivel TEXT, km_inicial INTEGER, data_aquisicao DATE, 
        valor_locacao REAL, usuario TEXT, cidade TEXT, crlv_path TEXT)""")
    
    # Check para adicionar a coluna se ela não existir em um banco antigo
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(veiculos)")
    cols = [info[1] for info in cursor.fetchall()]
    if 'crlv_path' not in cols:
        conn.execute("ALTER TABLE veiculos ADD COLUMN crlv_path TEXT")
    
    conn.commit()
    conn.close()
init_db()

# --- LOGIN ---
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

# --- DASHBOARD COM GESTÃO ---
def dashboard():
    st.title("📊 Painel Estratégico de Frota")
    conn = get_conn()
    df_v = pd.read_sql("SELECT * FROM veiculos", conn)
    df_d = pd.read_sql("SELECT * FROM despesas", conn)
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Custo Total", f"R$ {df_d['valor'].sum():,.2f}")
    c2.metric("Frota Ativa", f"{len(df_v[df_v['status']=='Ativo'])}")
    c3.metric("Manutenções", f"{len(df_v[df_v['status']=='Manutenção'])}")
    c4.metric("Total de Ativos", len(df_v))
    
    st.divider()
    
    # Gestão de Tabela
    st.subheader("Gerenciamento de Ativos")
    # Tabela Editável
    edited_df = st.data_editor(df_v, num_rows="dynamic", use_container_width=True)
    
    col_a, col_b = st.columns(2)
    if col_a.button("Salvar Edições"):
        edited_df.to_sql('veiculos', conn, if_exists='replace', index=False)
        st.success("Tabela atualizada!"); st.rerun()
        
    placa_del = col_b.text_input("Placa para Excluir permanentemente:")
    if col_b.button("Excluir Registro"):
        conn.execute("DELETE FROM veiculos WHERE placa = ?", (placa_del.upper(),))
        conn.commit(); st.warning(f"Registro {placa_del} excluído!"); st.rerun()
    
    conn.close()

# --- CADASTRO ---
def cadastro():
    st.title("➕ Cadastro de Veículo")
    with st.form("form_completo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        placa = c1.text_input("Placa").upper()
        marca = c2.text_input("Marca")
        modelo = c1.text_input("Modelo")
        status = c2.selectbox("Status", ["Ativo", "Manutenção", "Inativo"])
        comb = c1.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel S10", "Flex"])
        km = c2.number_input("KM Inicial", 0)
        dt_aq = c1.date_input("Data de Aquisição")
        valor = c2.number_input("Valor Locação (R$)", 0.0)
        user = c1.text_input("Usuário")
        cidade = c2.text_input("Cidade")
        
        # CAMPO NOVO: Upload do CRLV
        crlv = st.file_uploader("Upload do CRLV (PDF ou Imagem)", type=['pdf', 'jpg', 'png'])
        
        if st.form_submit_button("Salvar Ativo"):
            conn = get_conn()
            # Salva o nome do arquivo no banco
            crlv_nome = crlv.name if crlv else None
            
            conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (placa, marca, modelo, status, comb, km, dt_aq, valor, user, cidade, crlv_nome))
            conn.commit()
            conn.close()
            st.success("Ativo registrado com o CRLV!")
# --- NAVEGAÇÃO ---
st.sidebar.title(f"Olá, {st.session_state['perfil']}")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Cadastro", "Lançar Custo"])
if st.sidebar.button("Sair"): st.session_state['logado'] = False; st.rerun()

if menu == "Dashboard": dashboard()
elif menu == "Cadastro": cadastro()
elif menu == "Lançar Custo": 
    st.title("💰 Lançar Custo")
    # ... (Manter lógica de lançamento de custo)    
