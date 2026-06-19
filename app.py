import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import altair as alt

# Configuração da Página com Tema Escuro Nativo
st.set_page_config(page_title="FleetX - Gestão de Frotas", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. BANCO DE DADOS E INFRAESTRUTURA
# ==========================================
def conectar_db():
    conn = sqlite3.connect('frotas_codespace.db')
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
    
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO veiculos VALUES ('BRA2E19', 'Volvo FH 540', 92000, 'Disponível', 100000, 'Rota SP-RJ', 'Próprio', 'RENAVAM 0123456789')")
        cursor.execute("INSERT INTO veiculos VALUES ('ABC1234', 'Scania R450', 149500, 'Disponível', 150000, 'Rota SP-BH', 'Reserva', 'RENAVAM 9876543210')")
        cursor.execute("INSERT INTO motoristas VALUES ('João Silva', '12345678900', '2026-08-10', 'Sim')")
    conn.commit()
    return conn

conn = conectar_db()

DICIONARIO_MULTAS = {
    "7455-0": {"gravidade": "Média", "pontos": 4, "valor": 130.16, "desc": "Velocidade superior à máxima em até 20%"},
    "7463-0": {"gravidade": "Grave", "pontos": 5, "valor": 195.23, "desc": "Velocidade superior à máxima entre 20% e 50%"},
    "5010-0": {"gravidade": "Gravíssima", "pontos": 7, "valor": 880.41, "desc": "Dirigir sem CNH ou com CNH vencida"}
}

# ==========================================
# 2. TELA DE LOGIN & MENU LATERAL
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['perfil'] = None

if not st.session_state['autenticado']:
    st.title("🔑 FleetX - Autenticação")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar como Operador (Campo Rápido)", use_container_width=True):
            st.session_state['autenticado'] = True
            st.session_state['perfil'] = 'operador'
            st.rerun()
    with col2:
        if st.button("Entrar como Gestor (Painel Completo)", use_container_width=True):
            st.session_state['autenticado'] = True
            st.session_state['perfil'] = 'gestor'
            st.rerun()
else:
    st.sidebar.title("FleetX Control")
    st.sidebar.write(f"**Perfil ativo:** {st.session_state['perfil'].upper()}")
    
    opcoes_menu = ["📋 Checklist de Campo", "⛽ Abastecimento"]
    if st.session_state['perfil'] == 'gestor':
        opcoes_menu = [
            "📊 Dashboard & KPIs", 
            "🚗 Cadastros Gerais (Frota/Motoristas)", 
            "📋 Checklist de Campo", 
            "⛽ Abastecimento", 
            "🛠️ OS & Aprovações", 
            "⚠️ Multas Automatizadas", 
            "📝 Gestão de Contratos & Sinistros"
        ]
        
    escolha = st.sidebar.radio("Navegação:", opcoes_menu)
    
    if st.sidebar.button("🚪 Sair do Sistema", type="primary"):
        st.session_state['autenticado'] = False
        st.session_state['perfil'] = None
        st.rerun()

    # ==========================================
    # 3. MÓDULO: CADASTROS GERAIS
    # ==========================================
    if escolha == "🚗 Cadastros Gerais (Frota/Motoristas)":
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
                    else:
                        st.warning("Preencha Placa e Modelo.")
                        
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

    # ==========================================
    # 4. MÓDULO: CHECKLIST DE CAMPO
    # ==========================================
    elif escolha == "📋 Checklist de Campo":
        st.title("📋 Checklist Prático de Entrada e Saída")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        with st.form("form_checklist", clear_on_submit=True):
            placa = st.selectbox("Selecione a Placa", df_veiculos['placa'])
            tipo = st.selectbox("Tipo de Movimentação", ["Entrada de Oficina", "Saída de Oficina", "Novo Contrato", "Devolução", "Substituição"])
            km = st.number_input("Quilometragem (KM) Atual", min_value=0, step=1)
            combustivel = st.selectbox("Nível do Tanque", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
            pneus = st.radio("Condição dos Pneus", ["Ok (Acima de 1.6mm)", "Alerta (Careca / Troca Necessária)"])
            avarias = st.text_input("Avarias ou observações")
            operador = st.text_input("Nome do Operador")
            
            enviar = st.form_submit_button("Transmitir Checklist")
            if enviar:
                cursor = conn.cursor()
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute("INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) VALUES (?,?,?,?,?,?,?,?)",
                               (placa, tipo, km, combustivel, avarias, pneus, operador, data_atual))
                cursor.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (km, placa))
                conn.commit()
                st.success(f"✅ Checklist enviado! KM atualizado na base para {km} KM.")

    # ==========================================
    # 5. MÓDULO: ABASTECIMENTO
    # ==========================================
    elif escolha == "⛽ Abastecimento":
        st.title("⛽ Lançamento de Abastecimento")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        with st.form("form_abastecimento", clear_on_submit=True):
            placa = st.selectbox("Veículo", df_veiculos['placa'])
            valor = st.number_input("Valor Total (R$)", min_value=0.0, step=10.0)
            km = st.number_input("KM no ato", min_value=0)
            
            salvar = st.form_submit_button("Registrar Abastecimento")
            if salvar:
                cursor = conn.cursor()
                data_atual = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", (placa, valor, data_atual))
                cursor.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (km, placa))
                conn.commit()
                st.success("⛽ Gasto computado!")

    # ==========================================
    # 6. MÓDULO: OS & APROVAÇÕES
    # ==========================================
    elif escolha == "🛠️ OS & Aprovações":
        st.title("🛠️ Fluxo de Ordens de Serviço")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        tab1, tab2 = st.tabs(["Abrir Nova OS", "Fila de Aprovações"])
        with tab1:
            with st.form("form_os"):
                placa = st.selectbox("Veículo", df_veiculos['placa'])
                tipo_m = st.selectbox("Tipo", ["Preventiva (Revisão/Troca de Óleo)", "Corretiva"])
                desc = st.text_area("Descrição")
                custo = st.number_input("Custo Previsto (R$)", min_value=0.0)
                
                criar = st.form_submit_button("Gerar OS")
                if criar:
                    cursor = conn.cursor()
                    data_atual = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO ordens_servico (placa, tipo, descricao, custo, data) VALUES (?,?,?,?,?)", (placa, tipo_m, desc, custo, data_atual))
                    cursor.execute("UPDATE veiculos SET status = 'Em Manutenção' WHERE placa = ?", (placa,))
                    conn.commit()
                    st.warning(f"⚠️ Veículo {placa} alterado para 'Em Manutenção'.")
                    st.rerun()
                    
        with tab2:
            df_os = pd.read_sql_query("SELECT * FROM ordens_servico WHERE status != 'Encerrado'", conn)
            if df_os.empty:
                st.info("Nenhuma OS pendente.")
            else:
                for idx, row in df_os.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**OS #{row['id']}** - {row['placa']} | Custo: R$ {row['custo']} | **Status: {row['status']}**")
                    if row['status'] == 'Aguardando Aprovação':
                        if col2.button("✔️ Aprovar", key=f"ap_{row['id']}"):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE ordens_servico SET status = 'Em Andamento' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE veiculos SET status = 'Em Andamento' WHERE placa = ?", (row['placa'],))
                            conn.commit()
                            st.rerun()
                    elif row['status'] == 'Em Andamento':
                        if col3.button("🔒 Encerrar", key=f"en_{row['id']}"):
                            cursor = conn.cursor()
                            # Quando encerra a revisão, define a próxima revisão para daqui a 10.000 KM automáticos
                            cursor.execute("SELECT km_atual FROM veiculos WHERE placa = ?", (row['placa'],))
                            km_atual_v = cursor.fetchone()[0]
                            prox_revisao_nova = km_atual_v + 10000
                            
                            cursor.execute("UPDATE ordens_servico SET status = 'Encerrado' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE veiculos SET status = 'Disponível', km_proxima_revisao = ? WHERE placa = ?", (prox_revisao_nova, row['placa']))
                            cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Manutenção', ?, ?)", (row['placa'], row['custo'], row['data']))
                            conn.commit()
                            st.success("Revisão encerrada! Próxima meta estendida em +10.000 KM.")
                            st.rerun()

    # ==========================================
    # 7. MÓDULO: MULTAS AUTOMATIZADAS
    # ==========================================
    elif escolha == "⚠️ Multas Automatizadas":
        st.title("⚠️ Lançamento de Infrações")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        placa = st.selectbox("Veículo Infrator", df_veiculos['placa'])
        data_m = st.text_input("Data (DD/MM/AAAA)")
        endereco = st.text_input("Endereço / Rodovia")
        codigo = st.text_input("Código de Infração")
        
        if st.button("Processar Multa"):
            if codigo in DICIONARIO_MULTAS:
                info = DICIONARIO_MULTAS[codigo]
                cursor = conn.cursor()
                cursor.execute("INSERT INTO multas (placa, data, endereco, codigo, gravidade, pontos, valor, descricao) VALUES (?,?,?,?,?,?,?,?)",
                               (placa, data_m, endereco, codigo, info['gravidade'], info['pontos'], info['valor'], info['desc']))
                cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Multa', ?, ?)", (placa, info['valor'], data_m))
                conn.commit()
                st.success(f"🚨 Autopreenchido: {info['desc']} | Valor: R$ {info['valor']}")

    # ==========================================
    # 8. MÓDULO: CONTRATOS & SINISTROS
    # ==========================================
    elif escolha == "📝 Gestão de Contratos & Sinistros":
        st.title("📝 Custos Administrativos")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        tipo_c = st.selectbox("Tipo", ["Pedágio", "Sinistro", "Locação"])
        placa = st.selectbox("Veículo", df_veiculos['placa'])
        valor = st.number_input("Valor (R$)", min_value=0.0)
        
        if st.button("Salvar Registro"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, ?, ?, ?)", (placa, tipo_c, valor, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Custo integrado.")

    # ==========================================
    # 9. MÓDULO: DASHBOARD, KPIS E CONTROLE DE KM
    # ==========================================
    elif escolha == "📊 Dashboard & KPIs":
        st.title("📊 Painel Executivo de Tomada de Decisão")
        
        # --- TABELA DE CONTROLE DE KM SOLICITADA ---
        st.subheader("🚗 Painel de Controle de KM & Previsão de Revisões")
        st.caption("Acompanhamento em tempo real de quanto resta rodar antes da próxima parada preventiva (Troca de óleo de 10k em 10k KM).")
        
        # Busca dados das metas de KM
        df_frotakm = pd.read_sql_query("SELECT placa, modelo, km_atual, km_proxima_revisao, status FROM veiculos", conn)
        
        # Faz os cálculos matemáticos diretamente na tabela
        df_frotakm['KM Restante para Rodar'] = df_frotakm['km_proxima_revisao'] - df_frotakm['km_atual']
        
        # Cria uma coluna com o status do prazo
        def avaliar_prazo(restante):
            if restante <= 0:
                return "🚨 CRÍTICO - KM VENCIDO!"
            elif restante <= 1500:
                return "⚠️ ALERTA - Agendar Oficina"
            else:
                return "🟢 Seguro (Rodando)"
                
        df_frotakm['Status do Prazo'] = df_frotakm['KM Restante para Rodar'].apply(avaliar_prazo)
        
        # Organiza as colunas bonitas para exibição
        df_exibicao = df_frotakm[['placa', 'modelo', 'km_atual', 'km_proxima_revisao', 'KM Restante para Rodar', 'Status do Prazo', 'status']]
        df_exibicao.columns = ['Placa', 'Modelo', 'KM Atual', 'Meta da Próxima Revisão', 'KM Restante para Rodar', 'Status do Prazo', 'Status Operacional']
        
        st.dataframe(df_exibicao, use_container_width=True)
        
        st.divider()

        # --- ALERTAS RÁPIDOS ---
        col_al1, col_al2 = st.columns(2)
        with col_al1:
            for _, r in df_frotakm.iterrows():
                if r['KM Restante para Rodar'] <= 1500:
                    st.error(f"Bloqueio Preditivo: {r['placa']} restam apenas {r['KM Restante para Rodar']} KM antes da revisão!")
        with col_al2:
            df_mot = pd.read_sql_query("SELECT * FROM motoristas", conn)
            for _, r in df_mot.iterrows():
                venc = datetime.strptime(r['cnh_vencimento'], "%Y-%m-%d")
                if venc <= datetime.now() + timedelta(days=60):
                    st.warning(f"CNH Próxima do Vencimento: Condutor {r['nome']} vence em {venc.strftime('%d/%m/%Y')}")

        st.divider()

        # --- FINANCEIRO E GRÁFICOS ---
        df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
        total_geral = df_fin['valor'].sum() if not df_fin.empty else 0.0
        c_comb = df_fin[df_fin['tipo_custo'] == 'Combustível']['valor'].sum()
        c_man = df_fin[df_fin['tipo_custo'] == 'Manutenção']['valor'].sum()
        
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
        df_chk_rep = pd.read_sql_query("SELECT * FROM checklists", conn)
        st.download_button("Exportar Planilha de Checklists (CSV)", df_chk_rep.to_csv(index=False), "relatorio_checklists.csv", "text/csv")
