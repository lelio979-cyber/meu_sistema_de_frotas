import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import os
import altair as alt

# Configuração da Página com Design Fluido e Modo Escuro Nativo
st.set_page_config(
    page_title="FleetX - Sistema de Gestão Inteligente de Frotas", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Dicionário de Multas Completo e Técnico
if "DICIONARIO_MULTAS" not in locals():
    DICIONARIO_MULTAS = {
        "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Velocidade superior à máxima em até 20%"},
        "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "Velocidade superior à máxima entre 20% e 50%"},
        "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Dirigir sem CNH ou com CNH vencida"}
    }

# --- INFRAESTRUTURA DE BANCO DE DADOS ---
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
        cursor.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (gerar_hash("admin123"),))
    conn.commit()
    return conn

try:
    conn = conectar_db()
except Exception as e:
    st.error(f"Erro de infraestrutura de dados: {e}")
    st.stop()

# --- SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario_logado'] = ""
    st.session_state['perfil_logado'] = ""

if not st.session_state['autenticado']:
    st.title("🔑 FleetX - Governança Corporativa")
    with st.form("form_login"):
        input_usuario = st.text_input("ID do Usuário").strip().lower()
        input_senha = st.text_input("Senha de Acesso", type="password")
        if st.form_submit_button("Autenticar no Sistema", use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (input_usuario, gerar_hash(input_senha)))
            resultado = cursor.fetchone()
            if resultado:
                st.session_state['autenticado'] = True
                st.session_state['usuario_logado'] = input_usuario
                st.session_state['perfil_logado'] = resultado[0]
                st.rerun()
            else:
                st.error("Credenciais inválidas. Sistema bloqueado.")
    st.stop()

# --- MENU LATERAL E ALERTAS DE COMPLIANCE ---
st.sidebar.title("FleetX Control")
st.sidebar.markdown(f"👤 **Usuário:** `{st.session_state['usuario_logado']}`")
st.sidebar.markdown(f"🛡️ **Perfil:** `{st.session_state['perfil_logado'].upper()}`")
st.sidebar.markdown("---")

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
    
escolha = st.sidebar.radio("Navegação do Ecossistema:", opcoes_menu)

if st.sidebar.button("🚪 Desconectar Sistema", type="primary", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

# Carga de dados reativa para os seletores das páginas
try:
    df_veiculos_global = pd.read_sql_query("SELECT placa FROM veiculos", conn)
except Exception:
    df_veiculos_global = pd.DataFrame(columns=['placa'])

# Monitor proativo de CNH no Menu Lateral
try:
    df_cnh_check = pd.read_sql_query("SELECT nome, cnh_vencimento FROM motoristas", conn)
    if not df_cnh_check.empty:
        for idx, row in df_cnh_check.iterrows():
            venc = datetime.strptime(row['cnh_vencimento'], "%Y-%m-%d").date()
            dias = (venc - date.today()).days
            if dias < 0:
                st.sidebar.error(f"🚨 CNH VENCIDA: {row['nome']}")
            elif dias <= 30:
                st.sidebar.warning(f"⚠️ CNH a vencer ({dias}d): {row['nome']}")
except Exception:
    pass

# --- RENDERIZAÇÃO DAS PÁGINAS PROFISSIONAIS ---

if escolha == "📊 Dashboard & KPIs":
    st.title("📊 Painel Executivo & KPIs de Performance")
    
    # Cartões de Métricas no Topo
    c1, c2, c3 = st.columns(3)
    try:
        total_v = conn.cursor().execute("SELECT count(*) FROM veiculos").fetchone()[0]
        total_m = conn.cursor().execute("SELECT count(*) FROM motoristas").fetchone()[0]
        total_custo = conn.cursor().execute("SELECT sum(valor) FROM financeiro").fetchone()[0] or 0.0
        c1.metric("Frota Total Cadastrada", f"{total_v} Veículos")
        c2.metric("Motoristas Ativos", f"{total_m} Condutores")
        c3.metric("Custo Operacional Acumulado", f"R$ {total_custo:,.2f}")
    except Exception:
        pass
        
    st.markdown("---")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Disponibilidade e Status Operacional")
        df_status = pd.read_sql_query("SELECT status, count(*) as total FROM veiculos GROUP BY status", conn)
        if not df_status.empty:
            chart1 = alt.Chart(df_status).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('status:N', title='Status'),
                y=alt.Y('total:Q', title='Frota'),
                color=alt.Color('status:N', scale=alt.Scale(scheme='darkmulti'))
            ).properties(height=300)
            st.altair_chart(chart1, use_container_width=True)
            
    with col_g2:
        st.subheader("Análise de Desembolso de Combustível por Placa")
        df_comb = pd.read_sql_query("SELECT placa, sum(valor) as total FROM financeiro WHERE tipo_custo='Combustível' GROUP BY placa", conn)
        if not df_comb.empty:
            chart2 = alt.Chart(df_comb).mark_bar(color="#FF4B4B").encode(
                x=alt.X('placa:N', title='Veículo'),
                y=alt.Y('total:Q', title='Total Gasto (R$)')
            ).properties(height=300)
            st.altair_chart(chart2, use_container_width=True)

elif escolha == "📋 Auditoria Geral de Operações":
    st.title("📋 Central Consolidada de Auditoria e Histórico")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Checklists Realizados", "Fluxo Financeiro & Custos", 
        "Ordens de Serviço", "Histórico de Frota", "Fichas de Motoristas"
    ])
    
    with tab1:
        df = pd.read_sql_query("SELECT data, placa, tipo_movimentacao, km, combustivel, operador, avarias FROM checklists ORDER BY data DESC", conn)
        st.dataframe(df, use_container_width=True)
    with tab2:
        df = pd.read_sql_query("SELECT data, placa, tipo_custo, valor FROM financeiro ORDER BY data DESC", conn)
        st.dataframe(df, use_container_width=True)
    with tab3:
        df = pd.read_sql_query("SELECT id, data, placa, descricao, custo, status, aprovado_por FROM ordens_servico ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True)
    with tab4:
        df = pd.read_sql_query("SELECT placa, modelo, km_atual, status, km_proxima_revisao, tipo_frota, locadora_nome FROM veiculos", conn)
        st.dataframe(df, use_container_width=True)
    with tab5:
        df = pd.read_sql_query("SELECT nome, cnh_numero, cnh_vencimento, termo_aceite FROM motoristas", conn)
        st.dataframe(df, use_container_width=True)

elif escolha == "🚗 Cadastros Gerais (Frota/Motoristas)":
    st.title("🚗 Central de Cadastros e Gestão Avançada")
    tab_veic, tab_mot, tab_downloads = st.tabs(["Cadastrar Veículo & CRLV", "Cadastrar Motorista & CNH", "📥 Arquivo Digital"])
    
    with tab_veic:
        st.subheader("Entrada de Novo Ativo na Frota")
        tipo_f = st.selectbox("Modalidade da Frota", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        
        locadora_nome = None
        data_loc_str = None
        if tipo_f == "Locadora":
            c_l1, c_l2 = st.columns(2)
            with c_l1: locadora_nome = st.text_input("Nome da Companhia de Locação")
            with c_l2: data_loc_str = str(st.date_input("Início da Vigência do Contrato"))

        with st.form("form_veic", clear_on_submit=True):
            p = st.text_input("Placa Identificadora (Padrão Mercosul/Antigo)").upper().strip()
            m = st.text_input("Modelo / Marca / Ano")
            ki = st.number_input("Quilometragem Inicial Hodômetro", min_value=0)
            kr = st.number_input("Plano de Próxima Revisão (KM)", min_value=0)
            tr = st.text_input("Trecho Operacional / Base Destinada")
            doc = st.text_area("Observações Técnicas do Ativo")
            up_crlv = st.file_uploader("Upload do CRLV Digital (PDF/Imagem)", type=["pdf", "png", "jpg"])
            
            if st.form_submit_button("Salvar Veículo na Base de Dados"):
                if p and m:
                    blob = up_crlv.read() if up_crlv is not None else None
                    try:
                        conn.cursor().execute("INSERT INTO veiculos VALUES (?, ?, ?, 'Disponível', ?, ?, ?, ?, ?, ?, ?, NULL)",
                                       (p, m, ki, kr, tr, tipo_f, doc, blob, locadora_nome, data_loc_str))
                        conn.commit()
                        st.success(f"✅ Veículo {p} integrado com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Conflito de Sistema: Esta placa já existe na base.")

    with tab_mot:
        st.subheader("Registro de Condutor Autorizado")
        with st.form("form_mot", clear_on_submit=True):
            nome = st.text_input("Nome Completo do Profissional")
            cnh = st.text_input("Número do Registro da CNH")
            venc = st.date_input("Data de Vencimento da CNH")
            up_cnh = st.file_uploader("Upload da CNH Digital", type=["pdf", "png", "jpg"])
            up_termo = st.file_uploader("Upload do Termo de Uso Assinado", type=["pdf", "png", "jpg"])
            aceite = st.checkbox("Declaro que o condutor foi instruído sobre as normas internas de conformidade.")
            
            if st.form_submit_button("Efetivar Cadastro do Motorista"):
                if nome and cnh and aceite:
                    b_cnh = up_cnh.read() if up_cnh is not None else None
                    b_termo = up_termo.read() if up_termo is not None else None
                    conn.cursor().execute("INSERT INTO motoristas VALUES (?, ?, ?, 'Sim', ?, ?)", 
                                   (nome, cnh, str(venc), b_cnh, b_termo))
                    conn.commit()
                    st.success(f"👤 Motorista {nome} habilitado no sistema!")
                    st.rerun()

    with tab_downloads:
        st.subheader("Repositório Digital de Documentos")
        c = conn.cursor()
        c.execute("SELECT placa, arquivo_crlv FROM veiculos WHERE arquivo_crlv IS NOT NULL")
        linhas = c.fetchall()
        if linhas:
            for pl, blob in linhas:
                st.download_button(label=f"📥 Baixar CRLV Digital - {pl}", data=blob, file_name=f"CRLV_{pl}.pdf")
        else:
            st.info("Nenhum documento digital armazenado no momento.")

elif escolha == "👥 Controle de Usuários":
    st.title("👥 Controle de Perfis e Segurança de Acesso")
    with st.form("form_user", clear_on_submit=True):
        u = st.text_input("Nome de Usuário (Login)").strip().lower()
        s = st.text_input("Senha Corporativa", type="password")
        p = st.selectbox("Nível de Acesso / Hierarquia", ["Operador", "Gestor"])
        if st.form_submit_button("Gerar Nova Credencial"):
            if u and s:
                try:
                    conn.cursor().execute("INSERT INTO usuarios VALUES (?, ?, ?)", (u, gerar_hash(s), p))
                    conn.commit()
                    st.success("✅ Usuário provisionado no sistema!")
                except sqlite3.IntegrityError:
                    st.error("❌ Nome de usuário indisponível.")

elif escolha == "📍 Atualização de KM Diária":
    st.title("📍 Atualização Crítica de Quilometragem Diária")
    df_v = pd.read_sql_query("SELECT placa, km_atual FROM veiculos", conn)
    if not df_v.empty:
        with st.form("form_km_diario"):
            pl = st.selectbox("Selecione o Ativo", df_v['placa'])
            km_antigo = int(df_v[df_v['placa'] == pl]['km_atual'].values[0])
            st.info(f"Último registro deste veículo: {km_antigo} KM")
            novo_km = st.number_input("Quilometragem Atual do Painel", min_value=0)
            
            if st.form_submit_button("Validar e Atualizar Hodômetro"):
                if novo_km <= km_antigo:
                    st.error(f"Inconsistência: O novo KM não pode ser menor ou igual ao anterior ({km_antigo} KM).")
                else:
                    conn.cursor().execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (novo_km, pl))
                    conn.commit()
                    st.success("✅ Hodômetro atualizado e gravado.")
                    st.rerun()
    else:
        st.warning("Sem veículos cadastrados.")

elif escolha == "📋 Checklist de Campo":
    st.title("📋 Checklist de Campo e Movimentação")
    if not df_veiculos_global.empty:
        with st.form("form_checklist_avancado", clear_on_submit=True):
            pl = st.selectbox("Selecione a Placa", df_veiculos_global['placa'])
            tp = st.selectbox("Natureza da Movimentação", ["Entrada de Oficina", "Saída de Oficina", "Novo Contrato", "Devolução"])
            km = st.number_input("Quilometragem de Verificação", min_value=0)
            tk = st.selectbox("Nível do Tanque de Combustível", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
            pn = st.radio("Condição dos Pneus", ["Regular / Conforme", "Avaria / Substituir"])
            av = st.text_input("Apontar Avarias Visuais (Caso existam)")
            op = st.text_input("Operador Responsável", value=st.session_state['usuario_logado'], disabled=True)
            
            if st.form_submit_button("Submeter Relatório de Inspeção"):
                agora = datetime.now().strftime("%Y-%m-%d %H:%M")
                hoje = datetime.now().strftime("%Y-%m-%d")
                conn.cursor().execute("INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) VALUES (?,?,?,?,?,?,?,?)",
                               (pl, tp, km, tk, av, pn, op, agora))
                
                if tp == "Devolução":
                    cursor = conn.cursor()
                    cursor.execute("SELECT data_locacao, tipo_frota FROM veiculos WHERE placa = ?", (pl,))
                    dados = cursor.fetchone()
                    cursor.execute("UPDATE veiculos SET status = 'Disponível', data_devolucao = ? WHERE placa = ?", (hoje, pl))
                    if dados and dados[1] == "Locadora" and dados[0]:
                        d1 = datetime.strptime(dados[0], "%Y-%m-%d")
                        d2 = datetime.strptime(hoje, "%Y-%m-%d")
                        st.info(f"🔄 Ativo devolvido à locadora. Período de utilização: {abs((d2 - d1).days)} dias.")
                st.success("✅ Relatório de inspeção salvo com sucesso na auditoria.")
                conn.commit()
                st.rerun()
    else:
        st.warning("Cadastre ativos para liberar a inspeção.")

elif escolha == "⛽ Abastecimento":
    st.title("⛽ Lançamento e Controle Financeiro de Abastecimentos")
    if not df_veiculos_global.empty:
        with st.form("form_abast"):
            pl = st.selectbox("Ativo Beneficiado", df_veiculos_global['placa'])
            val = st.number_input("Desembolso Total Líquido (R$)", min_value=0.0)
            if st.form_submit_button("Lançar no Caixa Operacional"):
                if val > 0:
                    conn.cursor().execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", 
                                   (pl, val, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("⛽ Lançamento de combustível registrado!")
                    st.rerun()

elif escolha == "🛠️ OS & Aprovações":
    st.title("🛠️ Controle de Manutenções e Alocação de Recursos (O.S)")
    if not df_veiculos_global.empty:
        tab_abrir, tab_fila = st.tabs(["Abrir Nova Ordem de Serviço", "Fila de Despacho de Diretoria"])
        
        with tab_abrir:
            with st.form("form_gerar_os"):
                pl = st.selectbox("Selecione o Veículo", df_veiculos_global['placa'])
                tp = st.selectbox("Classificação Técnica", ["Preventiva", "Corretiva"])
                desc = st.text_area("Laudo Inicial / Escopo dos Serviços")
                custo = st.number_input("Custo Orçado Orçamento (R$)", min_value=0.0)
                if st.form_submit_button("Emitir Ordem de Serviço"):
                    conn.cursor().execute("INSERT INTO ordens_servico (placa, tipo, descricao, custo, status, data, aprovado_por, data_aprovacao) VALUES (?,?,?,?,'Aguardando Aprovação',?, NULL, NULL)", 
                                   (pl, tp, desc, custo, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("🛠️ Ordem de serviço inserida na fila de aprovação.")
                    
        with tab_fila:
            df_os = pd.read_sql_query("SELECT id, placa, tipo, descricao, custo, status FROM ordens_servico", conn)
            if not df_os.empty:
                st.dataframe(df_os, use_container_width=True)
                if st.session_state['perfil_logado'] == 'Gestor':
                    pendentes = df_os[df_os['status'] == 'Aguardando Aprovação']
                    if not pendentes.empty:
                        st.markdown("---")
                        st.subheader("Despacho de Governança")
                        id_os = st.selectbox("Selecione o ID da OS para Despacho", pendentes['id'])
                        resp = st.text_input("Assinatura Digital do Responsável", value=st.session_state['usuario_logado'].upper())
                        
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("👍 Autorizar Execução e Custos", type="primary"):
                                conn.cursor().execute("UPDATE ordens_servico SET status = 'Aprovado', aprovado_por = ?, data_aprovacao = ? WHERE id = ?", (resp, datetime.now().strftime("%Y-%m-%d %H:%M"), id_os))
                                # Lança automaticamente no financeiro o custo da OS aprovada
                                info_os = pendentes[pendentes['id'] == id_os].iloc[0]
                                conn.cursor().execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Manutenção', ?, ?)", (info_os['placa'], info_os['custo'], datetime.now().strftime("%Y-%m-%d")))
                                conn.commit()
                                st.success("OS Aprovada!")
                                st.rerun()
                        with col_b2:
                            if st.button("❌ Vetar / Recusar Serviço"):
                                conn.cursor().execute("UPDATE ordens_servico SET status = 'Rejeitado', aprovado_por = ?, data_aprovacao = ? WHERE id = ?", (resp
