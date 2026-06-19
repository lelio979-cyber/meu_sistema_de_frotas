import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import altair as alt
import hashlib

# Configuração da Página com Tema Escuro Nativo
st.set_page_config(page_title="FleetX - Gestão de Frotas", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. BANCO DE DADOS, SEGURANÇA E INFRAESTRUTURA
# ==========================================
def gerar_hash(senha):
    """Gera um hash SHA-256 seguro para armazenar a senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def conectar_db():
    conn = sqlite3.connect('frotas_codespace.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Tabela de Veículos
    cursor.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
        km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base Central', tipo_frota TEXT, documento TEXT)''')
    
    # Tabela de Checklists
    cursor.execute('''CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)''')
    
    # Tabela de Ordens de Serviço
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, 
        custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT)''')
    
    # Tabela Financeira
    cursor.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)''')
    
    # Tabela de Multas
    cursor.execute('''CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, data TEXT, endereco TEXT, 
        codigo TEXT, gravidade TEXT, pontos INTEGER, valor REAL, descricao TEXT)''')

    # Tabela de Motoristas
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT)''')
        
    # NOVA TABELA: Usuários com Login, Senha em Hash e Nível de Acesso
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)''')
    
    # Criar administrador padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        admin_senha_hash = gerar_hash("admin123")
        cursor.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (admin_senha_hash,))
        
    # Popular dados fictícios se os veículos estiverem vazios
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO veiculos VALUES ('BRA2E19', 'Volvo FH 540', 92000, 'Disponível', 100000, 'Rota SP-RJ', 'Próprio', 'RENAVAM 0123456789')")
        cursor.execute("INSERT INTO veiculos VALUES ('ABC1234', 'Scania R450', 149500, 'Disponível', 150000, 'Rota SP-BH', 'Reserva', 'RENAVAM 9876543210')")
        cursor.execute("INSERT INTO motoristas VALUES ('João Silva', '12345678900', '2026-08-10', 'Sim')")
        
    conn.commit()
    return conn

# Inicialização segura do banco de dados
try:
    conn = conectar_db()
except Exception as e:
    st.error(f"Erro de infraestrutura de banco de dados: {e}")

DICIONARIO_MULTAS = {
    "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Velocidade superior à máxima em até 20%"},
    "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "Velocidade superior à máxima entre 20% e 50%"},
    "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Dirigir sem CNH ou com CNH vencida"}
}

# ==========================================
# 2. SISTEMA DE AUTENTICAÇÃO (TELA DE LOGIN)
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario_logado'] = ""
    st.session_state['perfil_logado'] = ""

if not st.session_state['autenticado']:
    st.title("🔑 FleetX - Autenticação de Usuário")
    
    with st.form("form_login"):
        input_usuario = st.text_input("Usuário / Login").strip()
        input_senha = st.text_input("Senha", type="password")
        botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
        
        if botao_entrar:
            cursor = conn.cursor()
            hash_procurado = gerar_hash(input_senha)
            cursor.execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (input_usuario, hash_procurado))
            resultado = cursor.fetchone()
            
            if resultado:
                st.session_state['autenticado'] = True
                st.session_state['usuario_logado'] = input_usuario
                st.session_state['perfil_logado'] = resultado[0]
                st.success("Acesso autorizado! Carregando...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. (Acesso padrão inicial: admin / admin123)")
else:
    # ==========================================
    # 3. INTERFACE PRINCIPAL & MENU LATERAL
    # ==========================================
    st.sidebar.title("FleetX Control")
    st.sidebar.write(f"👤 **Usuário:** {st.session_state['usuario_logado']}")
    st.sidebar.write(f"🛡️ **Perfil:** {st.session_state['perfil_logado'].upper()}")
    
    # Filtro de menus dinâmico baseado no perfil carregado do banco de dados
    if st.session_state['perfil_logado'] == 'Gestor':
        opcoes_menu = [
            "📊 Dashboard & KPIs", 
            "🚗 Cadastros Gerais (Frota/Motoristas)", 
            "👥 Controle de Usuários",  # Novo menu exclusivo
            "📍 Atualização de KM Diária",
            "📋 Checklist de Campo", 
            "⛽ Abastecimento", 
            "🛠️ OS & Aprovações", 
            "⚠️ Multas Automatizadas", 
            "📝 Gestão de Contratos & Sinistros"
        ]
    else:
        # Menus restritos para perfil Operador
        opcoes_menu = ["📍 Atualização de KM Diária", "📋 Checklist de Campo", "⛽ Abastecimento"]
        
    escolha = st.sidebar.radio("Navegação:", opcoes_menu)
    
    if st.sidebar.button("🚪 Desconectar / Sair", type="primary"):
        st.session_state['autenticado'] = False
        st.session_state['usuario_logado'] = ""
        st.session_state['perfil_logado'] = ""
        st.rerun()

    # Leitura global auxiliar de veículos
    try:
        df_veiculos_global = pd.read_sql_query("SELECT placa FROM veiculos", conn)
    except Exception:
        df_veiculos_global = pd.DataFrame(columns=['placa'])

    # ==========================================
    # MÓDULOS DO SISTEMA
    # ==========================================
    if escolha == "📊 Dashboard & KPIs":
        st.title("📊 Painel Executivo de Tomada de Decisão")
        
        st.subheader("🚗 Painel de Controle de KM & Previsão de Revisões")
        df_frotakm = pd.read_sql_query("SELECT placa, modelo, km_atual, km_proxima_revisao, status FROM veiculos", conn)
        df_frotakm['KM Restante para Rodar'] = df_frotakm['km_proxima_revisao'] - df_frotakm['km_atual']
        
        def avaliar_prazo(restante):
            if restante <= 0:
                return "🚨 CRÍTICO - KM VENCIDO!"
            elif restante <= 1500:
                return "⚠️ ALERTA - Agendar Oficina"
            else:
                return "🟢 Seguro (Rodando)"
                
        df_frotakm['Status do Prazo'] = df_frotakm['KM Restante para Rodar'].apply(avaliar_prazo)
        df_exibicao = df_frotakm[['placa', 'modelo', 'km_atual', 'km_proxima_revisao', 'KM Restante para Rodar', 'Status do Prazo', 'status']]
        df_exibicao.columns = ['Placa', 'Modelo', 'KM Atual', 'Meta da Próxima Revisão', 'KM Restante para Rodar', 'Status do Prazo', 'Status Operacional']
        
        st.dataframe(df_exibicao, use_container_width=True)
        st.divider()

        col_al1, col_al2 = st.columns(2)
        with col_al1:
            for _, r in df_frotakm.iterrows():
                if r['KM Restante para Rodar'] <= 1500:
                    st.error(f"Bloqueio Preditivo: {r['placa']} restam apenas {r['KM Restante para Rodar']} KM antes da revisão!")
        with col_al2:
            df_mot = pd.read_sql_query("SELECT * FROM motoristas", conn)
            for _, r in df_mot.iterrows():
                try:
                    venc = datetime.strptime(r['cnh_vencimento'], "%Y-%m-%d")
                    if venc <= datetime.now() + timedelta(days=60):
                        st.warning
