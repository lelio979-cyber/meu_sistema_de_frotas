import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import os
import altair as alt

# Configuração da Página com Tema Escuro Nativo
st.set_page_config(page_title="FleetX - Gestão de Frotas", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# CONSTANTES E DICIONÁRIOS GLOBAL
# ==========================================
if "DICIONARIO_MULTAS" not in locals():
    DICIONARIO_MULTAS = {
        "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Velocidade superior à máxima em até 20%"},
        "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "Velocidade superior à máxima entre 20% e 50%"},
        "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Dirigir sem CNH ou com CNH vencida"}
    }

# ==========================================
# 1. BANCO DE DADOS E INFRAESTRUTURA
# ==========================================
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
    st.error(f"Erro ao inicializar banco de dados: {e}")
    st.stop()

# ==========================================
# 2. SISTEMA DE AUTENTICAÇÃO E NAVEGAÇÃO
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
    st.stop()

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ AUTENTICADO ---
st.sidebar.title("FleetX Control")
st.sidebar.write(f"👤 **Usuário:** {st.session_state['usuario_logado']}")
st.sidebar.write(f"🛡️ **Perfil:** {st.session_state['perfil_logado'].upper()}")

if st.session_state['perfil_logado'] == 'Gestor':
    opcoes_menu = [
        "📊 Dashboard & KPIs", 
        "📋 Auditoria Geral de Operações",
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
    opcoes_menu = [
        "📍 Atualização de KM Diária", 
        "📋 Checklist de Campo", 
        "⛽ Abastecimento",
        "📋 Auditoria Geral de Operações"
    ]
    
escolha = st.sidebar.radio("Navegação:", opcoes_menu)

if st.sidebar.button("🚪 Desconectar / Sair", type="primary"):
    st.session_state['autenticado'] = False
    st.rerun()

# Garantindo a carga global de veículos para evitar que as páginas quebrem
try:
    df_veiculos_global = pd.read_sql_query("SELECT placa FROM veiculos", conn)
except Exception:
    df_veiculos_global = pd.DataFrame(columns=['placa'])

# Alerta Proativo de Validação de CNH
try:
    df_cnh_check = pd.read_sql_query("SELECT nome, cnh_vencimento FROM motoristas", conn)
    if not df_cnh_check.empty:
        for idx, row in df_cnh_check.iterrows():
            venc = datetime.strptime(row['cnh_vencimento'], "%Y-%m-%d").date()
            dias_restantes = (venc - date.today()).days
            if dias_restantes < 0:
                st.sidebar.error(f"🚨 CNH de {row['nome']} VENCIDA!")
            elif dias_restantes <= 30:
                st.sidebar.warning(f"⚠️ CNH de {row['nome']} vence in {dias_restantes} dias.")
except Exception:
    pass

# ==========================================
# MÓDULOS DO SISTEMA
# ==========================================
if escolha == "📊 Dashboard & KPIs":
    st.title("📊 Painel Executivo & Tomada de Decisão")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição do Status da Frota")
        try:
            df_status = pd.read_sql_query("SELECT status, count(*) as total FROM veiculos GROUP BY status", conn)
            if not df_status.empty:
                graf_status = alt.Chart(df_status).mark_bar().encode(
                    x=alt.X('status:N', title='Status'),
                    y=alt.Y('total:Q', title='Quantidade de Veículos'),
                    color='status:N'
                ).properties(height=300)
                st.altair_chart(graf_status, use_container_width=True)
            else:
                st.info("Sem dados de status de frota.")
        except Exception as e:
            st.error(f"Erro ao carregar gráfico: {e}")
            
    with col2:
        st.subheader("Custos de Combustível por Veículo (R$)")
        try:
            df_comb = pd.read_sql_query("SELECT placa, sum(valor) as total_gasto FROM financeiro WHERE tipo_custo='Combustível' GROUP BY placa", conn)
            if not df_comb.empty:
                graf_comb = alt.Chart(df_comb).mark_bar().encode(
                    x=alt.X('placa:N', title='Veículo / Placa'),
                    y=alt.Y('total_gasto:Q', title='Total Gasto (R$)'),
                    color=alt.value("#FF4B4B")
                ).properties(height=300)
                st.altair_chart(graf_comb, use_container_width=True)
            else:
                st.info("Nenhum lançamento de combustível registrado.")
        except Exception as e:
            st.error(f"Erro ao carregar custos: {e}")

elif escolha == "📋 Auditoria Geral de Operações":
    st.title("📋 Tabela Consolidada de Histórico e Status Geral")
    tab_log1, tab_log2, tab_log3, tab_log4, tab_log5 = st.tabs([
        "Checklists Realizados", "Abastecimentos & Custos", "Ordens de Serviço", "Histórico de Veículos", "Histórico de Motoristas"
    ])
    
    with tab_log1:
        df_chk_log = pd.read_sql_query("SELECT data, placa, tipo_movimentacao, km, combustivel, operador, pneus_estado FROM checklists ORDER BY data DESC", conn)
        if not df_chk_log.empty:
            f_placa = st.text_input("Filtrar Checklists por Placa", key="f_chk_placa").upper().strip()
            if f_placa:
                df_chk_log = df_chk_log[df_chk_log['placa'].str.contains(f_placa)]
            st.dataframe(df_chk_log, use_container_width=True)
        else:
            st.info("Nenhum checklist registrado até o momento.")
            
    with tab_log2:
        df_fin_log = pd.read_sql_query("SELECT data, placa, tipo_custo, valor FROM financeiro ORDER BY data DESC", conn)
        if not df_fin_log.empty:
            f_tipo = st.multiselect("Filtrar por Tipo de Custo", options=df_fin_log['tipo_custo'].unique(), key="f_fin_tipo")
            if f_tipo:
                df_fin_log = df_fin_log[df_fin_log['tipo_custo'].isin(f_tipo)]
            st.dataframe(df_fin_log, use_container_width=True)
        else:
            st.info("Nenhum custo ou abastecimento lançado.")
            
    with tab_log3:
        df_os_log = pd.read_sql_query("SELECT id, data, placa, tipo, custo, status, aprovado_por, data_aprovacao FROM ordens_servico ORDER BY data DESC", conn)
        if not df_os_log.empty:
            f_status_os = st.multiselect("Filtrar OS por Status", options=df_os_log['status'].unique(), key="f_os_status")
            if f_status_os:
                df_os_log = df_os_log[df_os_log['status'].isin(f_status_os)]
            st.dataframe(df_os_log, use_container_width=True)
        else:
            st.info("Nenhuma ordem de serviço aberta.")

    with tab_log4:
        df_veic_log = pd.read_sql_query("SELECT placa, modelo, km_atual, status, km_proxima_revisao, tipo_frota, locadora_nome FROM veiculos", conn)
        if not df_veic_log.empty:
            st.dataframe(df_veic_log, use_container_width=True)
        else:
            st.info("Nenhum veículo cadastrado no sistema.")

    with tab_log5:
        df_mot_log = pd.read_sql_query("SELECT nome, cnh_numero, cnh_vencimento, termo_aceite FROM motoristas", conn)
        if not df_mot_log.empty:
            st.dataframe(df_mot_log, use_container_width=True)
        else:
            st.info("Nenhum motorista cadastrado no sistema.")

elif escolha == "🚗 Cadastros Gerais (Frota/Motoristas)":
    st.title("🚗 Central de Cadastros e Arquivos")
    tab_veic, tab_mot, tab_downloads = st.tabs(["Cadastrar Veículo & CRLV", "Cadastrar Motorista & CNH", "📥 Arquivo Digital (Downloads)"])
    
    with tab_veic:
        st.subheader("Inserir Novo Veículo")
        tipo_f = st.selectbox("Tipo de Frota", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        locadora_nome = None
        data_locacao_str = None
        
        if tipo_f == "Locadora":
            col_loc1, col_loc2 = st.columns(2)
            with col_loc1:
                locadora_nome = st.text_input("Nome da Locadora").strip()
            with col_loc2:
                data_locacao = st.date_input("Data de Início da Locação", value=date.today())
                data_locacao_str = str(data_locacao)

        with st.form("form_cadastro_veiculo", clear_on_submit=True):
            nova_placa = st.text_input("Placa do Veículo").upper()
            novo_modelo = st.text_input("Modelo / Marca")
            km_inicial = st.number_input("Quilometragem Inicial", min_value=0)
            km_revisao = st.number_input("KM da Próxima Revisão", min_value=0)
            trecho_inicial = st.text_input("Trecho Inicial")
            doc_veiculo = st.text_area("Informações Adicionais do Documento")
            upload_crlv = st.file_uploader("Upload do CRLV Digital", type=["pdf", "png", "jpg"])
            
            if st.form_submit_button("Salvar Veículo na Base"):
                if nova_placa and novo_modelo:
                    conteudo_crlv = upload_crlv.read() if upload_crlv is not None else None
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO veiculos VALUES (?, ?, ?, 'Disponível', ?, ?, ?, ?, ?, ?, ?, NULL)",
                                       (nova_placa, novo_modelo, km_inicial, km_revisao, trecho_inicial, tipo_f, doc_veiculo, conteudo_crlv, locadora_nome, data_locacao_str))
                        conn.commit()
                        st.success(f"✅ Veículo {nova_placa} cadastrado!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Essa placa já existe.")

    with tab_mot:
        st.subheader("Inserir Novo Motorista")
        with st.form("form_cadastro_motorista", clear_on_submit=True):
            nome_m = st.text_input("Nome Completo")
            cnh_m = st.text_input("Número da CNH")
            venc_cnh = st.date_input("Vencimento da CNH")
            upload_cnh = st.file_uploader("Upload da CNH Digital", type=["pdf", "png", "jpg"])
            upload_termo = st.file_uploader("Upload do Term
