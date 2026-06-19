import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import os
import altair as alt

# 1. Configuração de Página
st.set_page_config(
    page_title="FleetX - Gestão de Frotas", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

DICIONARIO_MULTAS = {
    "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Até 20%"},
    "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "20% a 50%"},
    "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Sem CNH"}
}

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_tabelas(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
        km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base Central', tipo_frota TEXT, 
        documento TEXT, arquivo_crlv BLOB, locadora_nome TEXT, data_locacao TEXT, data_devolucao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, 
        custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT, 
        aprovado_por TEXT, data_aprovacao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, data TEXT, endereco TEXT, 
        codigo TEXT, gravidade TEXT, pontos INTEGER, valor REAL, descricao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT,
        arquivo_cnh BLOB, arquivo_termo BLOB)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)''')

def conectar_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    cursor = conn.cursor()
    criar_tabelas(cursor)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        admin_senha_hash = gerar_hash("admin123")
        cursor.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (admin_senha_hash,))
    conn.commit()
    return conn

try:
    conn = conectar_db()
except Exception as e:
    st.error(f"Erro DB: {e}")
    st.stop()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario_logado'] = ""
    st.session_state['perfil_logado'] = ""

# 2. Tela de Autenticação
if not st.session_state['autenticado']:
    st.title("🔑 FleetX - Login")
    with st.form("form_login"):
        input_usuario = st.text_input("Usuário").strip().lower()
        input_senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            cursor = conn.cursor()
            hash_procurado = gerar_hash(input_senha)
            cursor.execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (input_usuario, hash_procurado))
            resultado = cursor.fetchone()
            if resultado:
                st.session_state['autenticado'] = True
                st.session_state['usuario_logado'] = input_usuario
                st.session_state['perfil_logado'] = resultado[0]
                st.rerun()
            else:
                st.error("Incorreto! Padrão: admin / admin123")
    st.stop()

# 3. Menu Lateral e Navegação
st.sidebar.title("FleetX Control")
st.sidebar.write(f"👤 {st.session_state['usuario_logado']}")
st.sidebar.write(f"🛡️ {st.session_state['perfil_logado'].upper()}")

if st.session_state['perfil_logado'] == 'Gestor':
    opcoes_menu = [
        "📊 Dashboard", 
        "📋 Auditoria",
        "🚗 Cadastros", 
        "👥 Usuários",  
        "📍 Atualizar KM",
        "📋 Checklist", 
        "⛽ Abastecimento", 
        "🛠️ OS", 
        "⚠️ Multas", 
        "📝 Contratos"
    ]
else:
    opcoes_menu = [
        "📍 Atualizar KM", 
        "📋 Checklist", 
        "⛽ Abastecimento",
        "📋 Auditoria"
    ]
    
escolha = st.sidebar.radio("Menu:", opcoes_menu)

if st.sidebar.button("🚪 Sair", type="primary"):
    st.session_state['autenticado'] = False
    st.rerun()

try:
    df_veiculos_global = pd.read_sql_query("SELECT placa FROM veiculos", conn)
except Exception:
    df_veiculos_global = pd.DataFrame(columns=['placa'])

# 4. Blocos de Conteúdo das Páginas
if escolha == "📊 Dashboard":
    st.title("📊 Painel")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Status")
        df_status = pd.read_sql_query("SELECT status, count(*) as total FROM veiculos GROUP BY status", conn)
        if not df_status.empty:
            g1 = alt.Chart(df_status).mark_bar().encode(x='status:N', y='total:Q')
            st.altair_chart(g1, use_container_width=True)
    with col2:
        st.subheader("Combustível")
        df_comb = pd.read_sql_query("SELECT placa, sum(valor) as total FROM financeiro WHERE tipo_custo='Combustível' GROUP BY placa", conn)
        if not df_comb.empty:
            g2 = alt.Chart(df_comb).mark_bar().encode(x='placa:N', y='total:Q')
            st.altair_chart(g2, use_container_width=True)

elif escolha == "📋 Auditoria":
    st.title("📋 Auditoria Geral")
    t1, t2, t3, t4, t5 = st.tabs(["Checklists", "Custos", "OS", "Veículos", "Motoristas"])
    with t1:
        st.dataframe(pd.read_sql_query("SELECT * FROM checklists", conn), use_container_width=True)
    with t2:
        st.dataframe(pd.read_sql_query("SELECT * FROM financeiro", conn), use_container_width=True)
    with t3:
        st.dataframe(pd.read_sql_query("SELECT * FROM ordens_servico", conn), use_container_width=True)
    with t4:
        st.dataframe(pd.read_sql_query("SELECT * FROM veiculos", conn), use_container_width=True)
    with t5:
        st.dataframe(pd.read_sql_query("SELECT * FROM motoristas", conn), use_container_width=True)

elif escolha == "🚗 Cadastros":
    st.title("🚗 Cadastros")
    v_tab, m_tab = st.tabs(["Veículo", "Motorista"])
    with v_tab:
        with st.form("f_v"):
            p = st.text_input("Placa").upper()
            m = st.text_input("Modelo")
            k = st.number_input("KM Inicial", min_value=0)
            if st.form_submit_button("Salvar Veículo"):
                conn.cursor().execute("INSERT INTO veiculos (placa, modelo, km_atual) VALUES (?,?,?)", (p,m,k))
                conn.commit()
                st.success("Salvo!")
                st.rerun()
    with m_tab:
        with st.form("f_m"):
            nome = st.text_input("Nome")
            cnh = st.text_input("CNH")
            venc = st.text_input("Vencimento (AAAA-MM-DD)")
            if st.form_submit_button("Salvar Motorista"):
                conn.cursor().execute("INSERT INTO motoristas (nome, cnh_numero, cnh_vencimento) VALUES (?,?,?)", (nome, cnh, venc))
                conn.commit()
                st.success("Salvo!")
                st.rerun()

elif escolha == "👥 Usuários":
    st.title("👥 Usuários")
    with st.form("f_u"):
        u = st.text_input("Usuário").lower()
        s = st.text_input("Senha", type="password")
        p = st.selectbox("Perfil", ["Operador", "Gestor"])
        if st.form_submit_button("Criar"):
            conn.cursor().execute("INSERT INTO usuarios VALUES (?,?,?)", (u, gerar_hash(s), p))
            conn.commit()
            st.success("Criado!")

elif escolha == "📍 Atualizar KM":
    st.title("📍 Atualizar KM")
    if not df_veiculos_global.empty:
        with st.form("f_k"):
            pl = st.selectbox("Veículo", df_veiculos_global['placa'])
            km = st.number_input("Novo KM", min_value=0)
            if st.form_submit_button("Atualizar"):
                conn.cursor().execute("UPDATE veiculos SET km_atual=? WHERE placa=?", (km, pl))
                conn.commit()
                st.success("Atualizado!")
                st.rerun()

elif escolha == "📋 Checklist":
    st.title("📋 Checklist")
    if not df_veiculos_global.empty:
        with st.form("f_c"):
            pl = st.selectbox("Placa", df_veiculos_global['placa'])
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            km = st.number_input("KM", min_value=0)
            tk = st.selectbox("Tanque", ["Cheio", "Meio", "Reserva"])
            op = st.text_input("Operador", value=st.session_state['usuario_logado'])
            if st.form_submit_button("Enviar"):
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.cursor().execute("INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, operador, data) VALUES (?,?,?,?,?,?)", (pl, tp, km, tk, op, dt))
                conn.commit()
                st.success("Enviado!")

elif escolha == "⛽ Abastecimento":
    st.title("⛽ Abastecimento")
    if not df_veiculos_global.empty:
        with st.form("f_a"):
            pl = st.selectbox("Placa", df_veiculos_global['placa'])
            val = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Registrar"):
                dt = datetime.now().strftime("%Y-%m-%d")
                conn.cursor().execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", (pl, val, dt))
                conn.commit()
                st.success("Registrado!")

elif escolha == "🛠️ OS":
    st.title("🛠️ Ordens de Serviço")
    if not df_veiculos_global.empty:
        with st.form("f_o"):
            pl = st.selectbox("Placa", df_veiculos_global['placa'])
            desc = st.text_input("Descrição")
            custo = st.number_input("Custo", min_value=0.0)
            if st.form_submit_button("Abrir OS"):
                dt = datetime.now().strftime("%Y-%m-%d")
                conn.cursor().execute("INSERT INTO ordens_servico (placa, descricao, custo, data) VALUES (?,?,?,?)", (pl, desc, custo, dt))
                conn.commit()
                st.success("Aberta!")

elif escolha == "⚠️ Multas":
    st.title("⚠️ Multas")
    if not df_veiculos_global.empty:
        with st.form("f_mult"):
            pl = st.selectbox("Placa", df_veiculos_global['placa'])
            cod = st.selectbox("Código", list(DICIONARIO_MULTAS.keys()))
            loc = st.text_input("Local")
            if st.form_submit_button("Registrar"):
                dt = datetime.now().strftime("%Y-%m-%d")
                inf = DICIONARIO_MULTAS[cod]
                conn.cursor().execute("INSERT INTO multas (placa, data, endereco, codigo, gravidade, pontos, valor, descricao) VALUES (?,?,?,?,?,?,?,?)", (pl, dt, loc, cod, inf['gravidade'], inf['pontos'], inf['valor'], inf['desc']))
                conn.commit()
                st.success("Registrada!")

elif escolha == "📝 Contratos":
    st.title("📝 Contratos & Sinistros")
    if not df_veiculos_global.empty:
        with st.form("f_con"):
            ev = st.selectbox("Tipo", ["Sinistro", "Pedágio", "Locação"])
            pl = st.selectbox("Placa", df_veiculos_global['placa'])
            val = st.number_input("Custo", min_value=0.0)
            if st.form_submit_button("Salvar"):
                dt = datetime.now().strftime("%Y-%m-%d")
                conn.cursor().execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?,?,?,?)", (pl, ev, val, dt))
                conn.commit()
                st.success("Salvo!")
