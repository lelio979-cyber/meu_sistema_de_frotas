import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import altair as alt
import hashlib
import os

# Configuração da Página com Tema Escuro Nativo
st.set_page_config(page_title="FleetX - Gestão de Frotas", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. BANCO DE DADOS, SEGURANÇA E INFRAESTRUTURA
# ==========================================
def gerar_hash(senha):
    """Gera um hash SHA-256 seguro para armazenar a senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_tabelas(cursor):
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
        
    # Tabela de Usuários
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)''')

def conectar_db():
    conn = sqlite3.connect('frotas_codespace.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Forçar criação inicial
    criar_tabelas(cursor)
    
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

# Inicialização auto-corretiva do banco de dados
try:
    conn = conectar_db()
except Exception as e:
    # Se houver incompatibilidade de tabelas antigas, remove o arquivo corrompido e cria um novo do zero
    if os.path.exists('frotas_codespace.db'):
        try:
            os.remove('frotas_codespace.db')
        except Exception:
            pass
    conn = conectar_db()

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
            try:
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
                    st.error("Usuário ou senha incorretos. (Acesso padrão: admin / admin123)")
            except Exception as err:
                st.error(f"Erro ao processar login: {err}. Tente recarregar a página.")
else:
    # ==========================================
    # 3. INTERFACE PRINCIPAL & MENU LATERAL
    # ==========================================
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
        st.session_state['usuario_logado'] = ""
        st.session_state['perfil_logado'] = ""
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
        st.subheader("🚗 Painel de Controle de KM & Previsão de Revisões")
        
        try:
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
                        st.error(f"Bloqueio Preditivo: {r['Placa']} restam apenas {r['KM Restante para Rodar']} KM antes da revisão!")
        except Exception as e:
            st.info("A aguardar dados operacionais.")

        with col_al2:
            try:
                df_mot = pd.read_sql_query("SELECT * FROM motoristas", conn)
                for _, r in df_mot.iterrows():
                    venc = datetime.strptime(r['cnh_vencimento'], "%Y-%m-%d")
                    if venc <= datetime.now() + timedelta(days=60):
                        st.warning(f"CNH Próxima do Vencimento: Condutor {r['nome']} vence em {venc.strftime('%d/%m/%Y')}")
            except Exception:
                pass

        st.divider()
        df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
        total_geral = df_fin['valor'].sum() if not df_fin.empty else 0.0
        c_comb = df_fin[df_fin['tipo_custo'] == 'Combustível']['valor'].sum() if not df_fin.empty else 0.0
        c_man = df_fin[df_fin['tipo_custo'] == 'Manutenção']['valor'].sum() if not df_fin.empty else 0.0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Custo Total de Operação", f"R$ {total_geral:,.2f}")
        kpi2.metric("Total Cartão Combustível", f"R$ {c_comb:,.2f}")
        kpi3.metric("Investimento em Oficinas", f"R$ {c_man:,.2f}")
        
        if not df_fin.empty:
            grafico_data = df_fin.groupby('tipo_custo')['valor'].sum().reset_index()
            chart = alt.Chart(grafico_data).mark_bar(color='#1f6aa5').encode(
                x=alt.X('tipo_custo:N', title='Natureza do Custo'),
                y=alt.Y('valor:Q', title='Total Acumulado (R$)')
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
        st.subheader("📥 Exportação de Relatórios Gerenciais")
        try:
            df_chk_rep = pd.read_sql_query("SELECT * FROM checklists", conn)
            st.download_button("Exportar Planilha de Checklists (CSV)", df_chk_rep.to_csv(index=False), "relatorio_checklists.csv", "text/csv")
        except Exception:
            st.write("Sem checklists para exportar no momento.")

    elif escolha == "🚗 Cadastros Gerais (Frota/Motoristas)":
        st.title("🚗 Central de Cadastros Corporativos")
        tab_veic, tab_mot = st.tabs(["Cadastrar Veículo & Documento", "Cadastrar Motorista & CNH"])
        
        with tab_veic:
            st.subheader("Inserir Novo Veículo na Frota")
            with st.form("form_cadastro_veiculo", clear_on_submit=True):
                nova_placa = st.text_input("Placa do Veículo", placeholder="Ex: BRA2E19").upper()
                novo_modelo = st.text_input("Modelo / Marca", placeholder="Ex: Volvo FH 540")
                km_inicial = st.number_input("Quilometragem Inicial", min_value=0, step=1000)
                km_revisao = st.number_input("KM da Próxima Revisão Preditiva", min_value=0, step=1000)
                trecho_inicial = st.text_input("Trecho Inicial de Operação", placeholder="Ex: Rota SP-RJ")
                tipo_f = st.selectbox("Tipo de Frota", ["Próprio", "Reserva", "Agregado / Terceirizado"])
                doc_veiculo = st.text_area("Informações do Documento do Veículo (RENAVAM / Chassi)")
                
                cadastrar_v = st.form_submit_button("Salvar Veículo na Base")
                if cadastrar_v:
                    if nova_placa and novo_modelo:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO veiculos VALUES (?, ?, ?, 'Disponível', ?, ?, ?, ?)",
                                           (nova_placa, novo_modelo, km_inicial, km_revisao, trecho_inicial, tipo_f, doc_veiculo))
                            conn.commit()
                            st.success(f"✅ Veículo {nova_placa} cadastrado com sucesso!")
                        except sqlite3.IntegrityError:
                            st.error("❌ Essa placa já está cadastrada.")
                        st.rerun()

        with tab_mot:
            st.subheader("Inserir Novo Motorista")
            with st.form("form_cadastro_motorista", clear_on_submit=True):
                nome_m = st.text_input("Nome Completo do Condutor")
                cnh_m = st.text_input("Número da CNH")
                venc_cnh = st.date_input("Data de Vencimento da CNH")
                st.write("---")
                st.caption("📜 Termo de Responsabilidade e Utilização de Veículo Corporativo")
                aceitou_termo = st.checkbox("O motorista leu e concorda expressamente com o Termo de Utilização")
                
                cadastrar_m = st.form_submit_button("Salvar Motorista")
                if cadastrar_m:
                    if nome_m and cnh_m and aceitou_termo:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO motoristas VALUES (?, ?, ?, 'Sim')", (nome_m, cnh_m, str(venc_cnh)))
                        conn.commit()
                        st.success(f"👤 Condutor {nome_m} salvo com sucesso!")
                    else:
                        st.error("Preencha todos os dados e valide o termo.")
                    st.rerun()

    elif escolha == "👥 Controle de Usuários":
        st.title("👥 Gestão de Acessos e Credenciais")
        tab_cad_user, tab_list_user = st.tabs(["Cadastrar Novo Usuário", "Usuários Ativos"])
        
        with tab_cad_user:
            st.subheader("Criar Login de Acesso")
            with st.form("form_cadastro_usuario", clear_on_submit=True):
                novo_login = st.text_input("Nome de Usuário (Login)").strip().lower()
                nova_senha = st.text_input("Senha de Acesso", type="password")
                perfil_escolhido = st.selectbox("Nível de Permissão", ["Operador", "Gestor"])
                
                salvar_user = st.form_submit_button("Cadastrar Usuário")
                if salvar_user:
                    if novo_login and nova_senha:
                        cursor = conn.cursor()
                        hash_senha_nova = gerar_hash(nova_senha)
                        try:
                            cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (novo_login, hash_senha_nova, perfil_escolhido))
                            conn.commit()
                            st.success(f"✅ Usuário '{novo_login}' criado com sucesso!")
                        except sqlite3.IntegrityError:
                            st.error("❌ Este utilizador já existe.")
                        st.rerun()
                        
        with tab_list_user:
            st.subheader("Gerenciar Contas Ativas")
            df_usuarios = pd.read_sql_query("SELECT usuario, perfil FROM usuarios", conn)
            for idx, r in df_usuarios.iterrows():
                col_u, col_p, col_b = st.columns([2, 2, 1])
                col_u.write(f"👤 **{r['usuario']}**")
                col_p.write(f"🏷️ Perfil: `{r['perfil']}`")
                if r['usuario'] == 'admin':
                    col_b.write("⚠️ *Protegido*")
                else:
                    if col_b.button("Remover", key=f"del_{r['usuario']}"):
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (r['usuario'],))
                        conn.commit()
                        st.rerun()

    elif escolha == "📍 Atualização de KM Diária":
        st.title("📍 Lançamento Rápido de KM Diário")
        df_veiculos = pd.read_sql_query("SELECT placa, modelo, km_atual FROM veiculos", conn)
        if df_veiculos.empty:
            st.warning("Nenhum veículo cadastrado.")
        else:
            with st.form("form_km_diario", clear_on_submit=True):
                lista_veiculos = [f"{row['placa']} - {row['modelo']} (Atual: {row['km_atual']} KM)" for _, row in df_veiculos.iterrows()]
                escolha_v = st.
