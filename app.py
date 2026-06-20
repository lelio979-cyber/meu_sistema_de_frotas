import streamlit as pd
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestão de Frotas Inteligente", layout="wide", page_icon="🚗")

# --- FUNÇÕES DE SEGURANÇA E CRIPTOGRAFIA ---
def ger_hash(senha):
    """Gera o hash SHA-256 de uma senha para armazenamento seguro."""
    return hashlib.sha256(senha.encode()).hexdigest()

# --- INICIALIZAÇÃO DO BANCO DE DADOS (V13) ---
def init_db():
    conn = sqlite3.connect('frotas_v13.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabela de Usuários
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)")
    
    # Tabela de Veículos
    c.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
            km_proxima_revisao INTEGER, trecho TEXT, tipo_frota TEXT, documento TEXT, ano INTEGER, 
            combustivel TEXT, cor TEXT, renavam TEXT, chassi TEXT, arquivo_crlv BLOB, 
            locadora_nome TEXT, capacidade_tanque INTEGER DEFAULT 50
        )
    """)
    
    # Tabela de Motoristas
    c.execute("""
        CREATE TABLE IF NOT EXISTS motoristas (
            nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT, 
            cpf TEXT, telefone TEXT, categoria_cnh TEXT, arquivo_cnh BLOB, arquivo_termo BLOB
        )
    """)
    
    # Tabela de Checklists e Auditoria
    c.execute("""
        CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
            combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT, 
            motorista TEXT, destino TEXT, finalidade TEXT, limpeza_interna TEXT, limpeza_externa TEXT, 
            inspecao_detalhada TEXT, foto_avaria BLOB, nivel_oleo TEXT, km_troca_oleo INTEGER, 
            numero_lacre TEXT, litros_abastecidos REAL, justificativa_horario TEXT, 
            pneu_di_esq TEXT, pneu_di_dir TEXT, pneu_tr_esq TEXT, pneu_tr_dir TEXT, arquivo_cupom BLOB
        )
    """)
    
    # Tabela do Financeiro
    c.execute("CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)")
    
    # Tabela de Ordens de Serviço (O.S.)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, custo REAL, 
            status TEXT DEFAULT 'Aguardando Aprovação', data TEXT, data_fim TEXT, 
            natureza_manutencao TEXT DEFAULT 'Corretiva', oficina_parceira TEXT, 
            pecas_substituidas TEXT, arquivo_nf BLOB
        )
    """)
    
    # Criação do usuário Administrador Padrão se o banco estiver limpo
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (ger_hash("admin123"),))
    
    conn.commit()
    return conn

conn = init_db()

# --- VERIFICAÇÃO DE ESQUEMA COMPLEMENTAR (MIGRAÇÃO DE SEGUNDA CAMADA) ---
try:
    conn.cursor().execute("ALTER TABLE ordens_servico ADD COLUMN natureza_manutencao TEXT DEFAULT 'Corretiva'")
    conn.cursor().execute("ALTER TABLE ordens_servico ADD COLUMN oficina_parceira TEXT")
    conn.cursor().execute("ALTER TABLE ordens_servico ADD COLUMN pecas_substituidas TEXT")
    conn.cursor().execute("ALTER TABLE ordens_servico ADD COLUMN arquivo_nf BLOB")
    conn.cursor().execute("ALTER TABLE ordens_servico ADD COLUMN data_fim TEXT")
    conn.commit()
except:
    pass

# ==============================================================================
# --- CENTRAL DE AUTENTICAÇÃO E SESSÃO ---
# ==============================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'u_log' not in st.session_state:
    st.session_state['u_log'] = None
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = 'Visualização'

if not st.session_state['autenticado']:
    st.title("🔐 Acesso ao Sistema de Frotas")
    with st.form(key="form_login_central"):
        usuario_input = st.text_input("Usuário").strip().lower()
        senha_input = st.text_input("Senha", type="password")
        botao_login = st.form_submit_button("Entrar")
        
        if botao_login:
            res = conn.cursor().execute("SELECT senha_hash, perfil FROM usuarios WHERE usuario = ?", (usuario_input,)).fetchone()
            if res and ger_hash(senha_input) == res[0]:
                st.session_state['autenticado'] = True
                st.session_state['u_log'] = usuario_input
                st.session_state['perfil'] = res[1]
                st.success("🎉 Autenticado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")
    st.stop()

# ==============================================================================
# --- CONTROLE DE MENUS POR PERFIL DE ACESSO (RBAC) ---
# ==============================================================================
perfil_usuario = st.session_state['perfil']

if perfil_usuario == "Gestor":
    opcoes_menu = ["🚗 Veículos", "👤 Motoristas", "📝 Checklist de Campo", "🛠️ Ordens de Serviço", "⛽ Abastecimento", "📋 Auditoria de Checklists", "👥 Gerenciamento de Usuários"]
elif perfil_usuario == "Operador":
    opcoes_menu = ["📝 Checklist de Campo", "⛽ Abastecimento"]
else:
    opcoes_menu = ["🚗 Veículos", "📋 Auditoria de Checklists"]

st.sidebar.markdown(f"👤 Logado como: **{st.session_state['u_log']}** (`{perfil_usuario}`)")
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state['autenticado'] = False
    st.session_state['u_log'] = None
    st.session_state['perfil'] = 'Visualização'
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Navegação", opcoes_menu)

# ==============================================================================
# --- MÓDULO: VEÍCULOS ---
# ==============================================================================
if menu == "🚗 Veículos":
    st.title("🚗 Gestão de Veículos da Frota")
    
    with st.form("f_veiculo_limpo"):
        st.markdown("##### Cadastrar Novo Veículo")
        c1, c2, c3 = st.columns(3)
        with c1:
            placa = st.text_input("Placa").strip().upper()
            modelo = st.text_input("Modelo/Versão")
        with c2:
            km_inicial = st.number_input("Odômetro Inicial (KM)", min_value=0, step=1)
            combustivel = st.selectbox("Combustível Padrão", ["Gasolina", "Etanol", "Diesel", "Flex", "GNV", "Elétrico"])
        with c3:
            capacidade_t = st.number_input("Capacidade do Tanque (Litros)", min_value=1, value=50, step=1)
            
        if st.form_submit_button("Salvar Registro"):
            if perfil_usuario == "Visualização":
                st.error("❌ Acesso Negado: Seu perfil não tem permissão para cadastrar dados.")
            elif not placa or not modelo:
                st.error("❌ Preencha os campos obrigatórios (Placa e Modelo).")
            else:
                try:
                    conn.cursor().execute(
                        "INSERT INTO veiculos (placa, modelo, km_atual, combustivel, capacidade_tanque) VALUES (?, ?, ?, ?, ?)",
                        (placa, modelo, km_inicial, combustivel, capacidade_t)
                    )
                    conn.commit()
                    st.success("🎉 Veículo registrado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Esta placa já se encontra cadastrada no sistema.")

    st.markdown("---")
    st.subheader("📋 Frota Cadastrada")
    df_v = pd.read_sql_query("SELECT placa as [Placa], modelo as [Modelo], km_atual as [KM Atual], combustivel as [Combustível], capacidade_tanque as [Tanque (L)] FROM veiculos", conn)
    st.dataframe(df_v, use_container_width=True, hide_index=True)

# ==============================================================================
# --- MÓDULO: MOTORISTAS ---
# ==============================================================================
elif menu == "👤 Motoristas":
    st.title("👤 Cadastro de
