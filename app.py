import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
import os

# Configuração da Página com Tema Escuro Nativo
st.set_page_config(page_title="FleetX - Gestão de Frotas", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# CONSTANTES E DICIONÁRIOS GLOBAL (Correção do Erro)
# ==========================================
DICIONARIO_MULTAS = {
    "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Velocidade superior à máxima em até 20%"},
    "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "Velocidade superior à máxima entre 20% e 50%"},
    "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Dirigir sem CNH ou com CNH vencida"}
}

# ==========================================
# 1. BANCO DE DADOS, SEGURANÇA E INFRAESTRUTURA
# ==========================================
def gerar_hash(senha):
    """Gera um hash SHA-256 seguro para armazenar a senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_tabelas(cursor):
    # Tabela de Veículos (9 colunas)
    cursor.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
        km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base Central', tipo_frota TEXT, 
        documento TEXT, arquivo_crlv BLOB)''')
    
    # Tabela de Checklists (9 colunas)
    cursor.execute('''CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)''')
    
    # Tabela de Ordens de Serviço (7 colunas)
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

    # Tabela de Motoristas (6 colunas)
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT,
        arquivo_cnh BLOB, arquivo_termo BLOB)''')
        
    # Tabela de Usuários
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)''')

def conectar_db():
    # Atualizado para v5 para garantir isolamento absoluto e tabelas limpas
    conn = sqlite3.connect('frotas_v5.db', check_same_thread=False)
    cursor = conn.cursor()
    criar_tabelas(cursor)
    
    # Garante usuário administrador padrão
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        admin_senha_hash = gerar_hash("admin123")
        cursor.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (admin_senha_hash,))
        
    conn.commit()
    return conn

# Inicialização segura
try:
    conn = conectar_db()
except Exception as e:
    st.error(f"Erro ao inicializar banco de dados: {e}")
    st.stop()

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
        input_usuario = st.text_input("Usuário / Login").strip().lower()
        input_senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema", use_container_width=True):
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
                st.error("Usuário ou senha incorretos. (Padrão: admin / admin123)")
else:
    # Menu lateral completo com todas as abas originais restabelecidas
    st.sidebar.title("FleetX Control")
    st.sidebar.write(f"👤 **Usuário:** {st.session_state['usuario_logado']}")
    st.sidebar.write(f"🛡️ **Perfil:** {st.session_state['perfil_logado'].upper()}")
    
    if st.session_state['perfil_logado'] == 'Gestor':
        opcoes_menu = [
            "📊 Dashboard & KPIs", 
            "🚗 Cadastros Gerais (Frota/Motoristas)", 
            "👥 Controle de Usuários",  
            "📍 Atualização de KM Diária",
            "📋 Checklist de Campo", 
            "⛽ Abastecimento", 
            "🛠️ OS & Aprovações", 
            "⚠️ Multas Automatizadas", 
            "📝 Gestão de Contratos & Sinistros"
        ]
    else:
        opcoes_menu = ["📍 Atualização de KM Diária", "📋 Checklist de Campo", "⛽ Abastecimento"]
        
    escolha = st.sidebar.radio("Navegação:", opcoes_menu)
    
    if st.sidebar.button("🚪 Desconectar / Sair", type="primary"):
        st.session_state['autenticado'] = False
        st.rerun()

    try:
        df_veiculos_global = pd.read_sql_query("SELECT placa FROM veiculos", conn)
    except Exception:
        df_veiculos_global = pd.DataFrame(columns=['placa'])

    # ==========================================
    # MÓDULOS DO SISTEMA
    # ==========================================
    if escolha == "📊 Dashboard & KPIs":
        st.title("📊 Painel Executivo de Tomada de Decisão")
        try:
            df_frotakm = pd.read_sql_query("SELECT placa, modelo, km_atual, km_proxima_revisao, status FROM veiculos", conn)
            st.dataframe(df_frotakm, use_container_width=True)
        except Exception:
            st.info("Nenhum dado operacional disponível para exibição no momento.")

    elif escolha == "🚗 Cadastros Gerais (Frota/Motoristas)":
        st.title("🚗 Central de Cadastros Corporativos")
        tab_veic, tab_mot = st.tabs(["Cadastrar Veículo & Documento", "Cadastrar Motorista & CNH"])
        
        with tab_veic:
            st.subheader("Inserir Novo Veículo e CRLV")
            with st.form("form_cadastro_veiculo", clear_on_submit=True):
                nova_placa = st.text_input("Placa do Veículo").upper()
                novo_modelo = st.text_input("Modelo / Marca")
                km_inicial = st.number_input("Quilometragem Inicial", min_value=0)
                km_revisao = st.number_input("KM da Próxima Revisão", min_value=0)
                trecho_inicial = st.text_input("Trecho Inicial")
                tipo_f = st.selectbox("Tipo de Frota", ["Próprio", "Reserva", "Terceirizado"])
                doc_veiculo = st.text_area("Informações Adicionais do Documento")
                
                upload_crlv = st.file_uploader("Upload do CRLV Digital (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
                
                if st.form_submit_button("Salvar Veículo na Base"):
                    if nova_placa and novo_modelo:
                        conteudo_crlv = upload_crlv.read() if upload_crlv is not None else None
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO veiculos VALUES (?, ?, ?, 'Disponível', ?, ?, ?, ?, ?)",
                                           (nova_placa, novo_modelo, km_inicial, km_revisao, trecho_inicial, tipo_f, doc_veiculo, conteudo_crlv))
                            conn.commit()
                            st.success(f"✅ Veículo {nova_placa} cadastrado com o CRLV anexado!")
                        except sqlite3.IntegrityError:
                            st.error("❌ Essa placa já existe no sistema.")
                        st.rerun()

        with tab_mot:
            st.subheader("Inserir Novo Motorista com Anexos")
            with st.form("form_cadastro_motorista", clear_on_submit=True):
                nome_m = st.text_input("Nome Completo")
                cnh_m = st.text_input("Número da CNH")
                venc_cnh = st.date_input("Vencimento da CNH")
                
                upload_cnh = st.file_uploader("Upload da CNH Digital (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
                upload_ter
