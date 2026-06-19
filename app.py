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
        documento TEXT, arquivo_crlv BLOB)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, 
        custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT)''')
    
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
    conn = sqlite3.connect('frotas_v5.db', check_same_thread=False)
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
# 2. SISTEMA DE AUTENTICAÇÃO
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

    # Alerta Proativo de Validação de CNH no topo do painel
    try:
        df_cnh_check = pd.read_sql_query("SELECT nome, cnh_vencimento FROM motoristas", conn)
        if not df_cnh_check.empty:
            for idx, row in df_cnh_check.iterrows():
                venc = datetime.strptime(row['cnh_vencimento'], "%Y-%m-%d").date()
                dias_restantes = (venc - date.today()).days
                if dias_restantes < 0:
                    st.sidebar.error(f"🚨 CNH de {row['nome']} VENCIDA!")
                elif dias_restantes <= 30:
                    st.sidebar.warning(f"⚠️ CNH de {row['nome']} vence em {dias_restantes} dias.")
    except Exception:
        pass

    # ==========================================
    # MÓDULOS DO SISTEMA COM AS MELHORIAS
    # ==========================================
    if escolha == "📊 Dashboard & KPIs":
        st.title("📊 Painel Executivo & Tomada de Decisão")
        
        # 1. Gráficos em Linha/Coluna Reais
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
                st.error(f"Erro ao carregar gráfico de status: {e}")
                
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

        st.markdown("---")
        st.subheader("🔍 Filtros Avançados & Relatórios Exportáveis")
        
        # 2. Filtros e Relatórios
        try:
            df_mestre = pd.read_sql_query("SELECT placa, modelo, km_atual, km_proxima_revisao, status, tipo_frota FROM veiculos", conn)
            if not df_mestre.empty:
                filtro_placa = st.text_input("Filtrar por Placa").upper().strip()
                filtro_status = st.multiselect("Filtrar por Status", options=df_mestre['status'].unique())
                
                df_filtrado = df_mestre.copy()
                if filtro_placa:
                    df_filtrado = df_filtrado[df_filtrado['placa'].str.contains(filtro_placa)]
                if filtro_status:
                    df_filtrado = df_filtrado[df_filtrado['status'].isin(filtro_status)]
                
                st.dataframe(df_filtrado, use_container_width=True)
                
                # Conversão nativa para CSV (Download de relatórios)
                csv = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar Relatório Customizado (CSV)",
                    data=csv,
                    file_name=f"relatorio_frota_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("Nenhum veículo disponível para geração de relatórios.")
        except Exception as e:
            st.error(f"Erro nos relatórios: {e}")

    elif escolha == "🚗 Cadastros Gerais (Frota/Motoristas)":
        st.title("🚗 Central de Cadastros e Arquivos")
        tab_veic, tab_mot, tab_downloads = st.tabs(["Cadastrar Veículo & CRLV", "Cadastrar Motorista & CNH", "📥 Arquivo Digital (Downloads)"])
        
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
                upload_termo = st.file_uploader("Upload do Termo de Utilização Assinado (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
                aceitou_termo = st.checkbox("Confirmo que o condutor aceitou as políticas de conformidade da frota")
                
                if st.form_submit_button("Salvar Motorista"):
                    if nome_m and cnh_m and aceitou_termo:
                        conteudo_cnh = upload_cnh.read() if upload_cnh is not None else None
                        conteudo_termo = upload_termo.read() if upload_termo is not None else None
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO motoristas VALUES (?, ?, ?, 'Sim', ?, ?)", 
                                           (nome_m, cnh_m, str(venc_cnh), conteudo_cnh, conteudo_termo))
                            conn.commit()
                            st.success(f"👤 Condutor {nome_m} salvo com os documentos arquivados com segurança!")
                        except Exception as e:
                            st.error(f"Erro ao salvar motorista: {e}")
                    else:
                        st.error("Por favor, preencha os dados e confirme o termo antes de salvar.")
                    st.rerun()

        with tab_downloads:
            st.subheader("Download e Visualização de Ficheiros BLOB")
            # 3. Download e Visualização de Arquivos Restabelecidos
            col_down1, col_down2 = st.columns(2)
            
            with col_down1:
                st.write("📂 **CRLV por Veículo**")
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT placa, arquivo_crlv FROM veiculos WHERE arquivo_crlv IS NOT NULL")
                    veiculos_com_doc = cursor.fetchall()
                    if veiculos_com_doc:
                        for p, blob in veiculos_com_doc:
                            st.download_button(label=f"📥 Baixar CRLV - {p}", data=blob, file_name=f"CRLV_{p}.pdf", mime="application/octet-stream")
                    else:
                        st.info("Nenhum CRLV armazenado no momento.")
                except Exception as e:
                    st.error(f"Erro ao ler CRLV: {e}")
                    
            with col_down2:
                st.write("📂 **CNH por Condutor**")
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT nome, arquivo_cnh FROM motoristas WHERE arquivo_cnh IS NOT NULL")
                    motoristas_com_doc = cursor.fetchall()
                    if motoristas_com_doc:
                        for n, blob in motoristas_com_doc:
                            st.download_button(label=f"📥 Baixar CNH - {n}", data=blob, file_name=f"CNH_{n}.pdf", mime="application/octet-stream")
                    else:
                        st.info("Nenhuma CNH armazenada no momento.")
                except Exception as e:
                    st.error(f"Erro ao ler CNH: {e}")

    elif escolha == "👥 Controle de Usuários":
        st.title("👥 Gestão de Acessos e Credenciais")
        tab_cad_user, tab_list_user = st.tabs(["Cadastrar Novo Usuário", "Usuários Ativos"])
        with tab_cad_user:
            with st.form("form_cadastro_usuario", clear_on_submit=True):
                novo_login = st.text_input("Nome de Usuário (Login)").strip().lower()
                nova_senha = st.text_input("Senha de Acesso", type="password")
                perfil_escolhido = st.selectbox("Nível de Permissão", ["Operador", "Gestor"])
                if st.form_submit_button("Cadastrar Usuário"):
                    if novo_login and nova_senha:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (novo_login, gerar_hash(nova_senha), perfil_escolhido))
                            conn.commit()
                            st.success(f"✅ Usuário '{novo_login}' criado!")
                        except sqlite3.IntegrityError:
                            st.error("❌ Usuário já existe.")
                        st.rerun()
        with tab_list_user:
            df_usuarios = pd.read_sql_query("SELECT usuario, perfil FROM usuarios", conn)
            st.dataframe(df_usuarios, use_container_width=True)

    elif escolha == "📍 Atualização de KM Diária":
        st.title("📍 Lançamento Rápido de KM Diário")
        df_veiculos = pd.read_sql_query("SELECT placa, modelo, km_atual FROM veiculos", conn)
        if not df_veiculos.empty:
            with st.form("form_km"):
                escolha_v = st.selectbox("Selecione o Veículo", df_veiculos['placa'])
                novo_km = st.number_input("Novo KM", min_value=0)
                
                # Obtém o KM atual salvo no banco de dados para a validação inteligente
                km_atual_banco = int(df_veiculos[df_veiculos['placa'] == escolha_v]['km_atual'].values[0])
                
                if st.form_submit_button("Atualizar"):
                    # 4. Validação Inteligente de KM
                    if novo_km <= km_atual_banco:
                        st.error(f"❌ Erro de Consistência: O novo KM ({novo_km}) não pode ser menor ou igual ao KM atual do veículo ({km_atual_banco}).")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (novo_km, escolha_v))
                        conn.commit()
                        st.success(f"✅ KM do veículo {escolha_v} atualizado com sucesso!")
                        st.rerun()

    elif escolha == "📋 Checklist de Campo":
        st.title("📋 Checklist Prático de Entrada e Saída")
        if not df_veiculos_global.empty:
            with st.form("form_chk", clear_on_submit=True):
                placa = st.selectbox("Placa", df_veiculos_global['placa'])
                tipo = st.selectbox("Movimentação", ["Entrada de Oficina", "Saída de Oficina", "Novo Contrato", "Devolução"])
                km = st.number_input("Quilometragem", min_value=0)
                combustivel = st.selectbox("Nível do Tanque", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
                pneus = st.radio("Condição dos Pneus", ["Ok", "Alerta"])
                avarias = st.text_input("Avarias observadas")
                operador = st.text_input("Nome do Operador")
                
                if st.form_submit_button("Enviar Checklist"):
                    cursor = conn.cursor()
                    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cursor.execute('''INSERT INTO checklists 
                                   (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) 
                                   VALUES (?,?,?,?,?,?,?,?)''',
                                   (placa, tipo, km, combustivel, avarias, pneus, operador, data_atual))
                    conn.commit()
                    st.success("✅ Checklist enviado e sincronizado com sucesso!")
                    st.rerun()

    elif escolha == "⛽ Abastecimento":
        st.title("⛽ Lançamento de Abastecimento")
        if not df_veiculos_global.empty:
            with st.form("form_abs"):
                placa = st.selectbox("Veículo", df_veiculos_global['placa'])
                valor = st.number_input("Valor Total (R$)", min_value=0.0)
                if st.form_submit_button("Registrar"):
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", 
                                   (placa, valor, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Registrado!")

    elif escolha == "🛠️ OS & Aprovações":
        st.title("🛠️ Fluxo de Ordens de Serviço")
        if df_veiculos_global.empty:
            st.warning("Cadastre um veículo antes.")
        else:
            tab1, tab2 = st.tabs(["Abrir Nova OS", "Fila de Aprovações"])
            with tab1:
                with st.form("form_os"):
                    placa = st.selectbox("Veículo", df_veiculos_global['placa'])
                    tipo_m = st.selectbox("Tipo", ["Preventiva", "Corretiva"])
                    desc = st.text_area("Descrição")
                    custo = st.number_input("Custo Previsto (R$)", min_value=0.0)
                    if st.form_submit_button("Gerar OS"):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO ordens_servico (placa, tipo, descricao, custo, status, data) VALUES (?,?,?,?,'Aguardando Aprovação',?)", 
                                       (placa, tipo_m, desc, custo, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("Ordem de serviço aberta!")
            with tab2:
                df_os = pd.read_sql_query("SELECT * FROM ordens_servico", conn)
                st.dataframe(df_os, use_container_width=True)

    elif escolha == "⚠️ Multas Automatizadas":
        st.title("⚠️ Lançamento de Infrações")
        if df_veiculos_global.empty:
            st.warning("Cadastre veículos antes.")
        else:
            with st.form("form_multas"):
                placa = st.selectbox("Veículo Infrator", df_veiculos_global['placa'])
                data_m = st.text_input("Data (DD/MM/AAAA)")
                endereco = st.text_input("Endereço")
                codigo = st.selectbox("Código de Infração", list(DICIONARIO_MULTAS.keys()))
                if st.form_submit_button("Processar Multa"):
                    info = DICIONARIO_MULTAS[codigo]
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO multas (placa, data, endereco, codigo, gravidade, pontos, valor, descricao) VALUES (?,?,?,?,?,?,?,?)",
                                   (placa, data_m, endereco, codigo, info['gravidade'], info['pontos'], info['valor'], info['desc']))
                    conn.commit()
                    st.success("🚨 Multa processada com sucesso!")

    elif escolha == "📝 Gestão de Contratos & Sinistros":
        st.title("📝 Lançamentos Administrativos & Sinistros")
        if df_veiculos_global.empty:
            st.warning("Não há veículos na frota.")
        else:
            with st.form("form_admin"):
                tipo_c = st.selectbox("Natureza do Evento", ["Sinistro", "Pedágio", "Locação"])
                placa = st.selectbox("Veículo Vinculado", df_veiculos_global['placa'])
                valor = st.number_input("Custo Financeiro (R$)", min_value=0.0)
                if st.form_submit_button("Salvar Registro"):
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, ?, ?, ?)", 
                                   (placa, tipo_c, valor, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("✅ Registro administrativo devido e salvo.")
