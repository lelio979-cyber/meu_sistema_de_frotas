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
    
    # Tabela de Veículos (Atualizada com Documento)
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

    # Tabela de Motoristas (Atualizada com Termo e CNH)
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT)''')
    
    # Inserções Iniciais para Testes se vazio
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO veiculos VALUES ('BRA2E19', 'Volvo FH 540', 92000, 'Disponível', 100000, 'Rota SP-RJ', 'Próprio', 'RENAVAM 0123456789')")
        cursor.execute("INSERT INTO veiculos VALUES ('ABC1234', 'Scania R450', 149500, 'Disponível', 150000, 'Rota SP-BH', 'Reserva', 'RENAVAM 9876543210')")
        cursor.execute("INSERT INTO motoristas VALUES ('João Silva', '12345678900', '2026-08-10', 'Aceito')")
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
    # 3. MÓDULO NOVO: CADASTROS GERAIS (GESTOR)
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
                
                # Campo solicitado para o Documento do veículo
                doc_veiculo = st.text_area("Informações do Documento do Veículo (RENAVAM / Chassi / Licenciamento)")
                
                cadastrar_v = st.form_submit_button("Salvar Veículo na Base")
                if cadastrar_v:
                    if nova_placa and novo_modelo:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO veiculos VALUES (?, ?, ?, 'Disponível', ?, ?, ?, ?)",
                                           (nova_placa, novo_modelo, km_inicial, km_revisao, trecho_inicial, tipo_f, doc_veiculo))
                            conn.commit()
                            st.success(f"✅ Veículo {nova_placa} cadastrado e integrado com sucesso!")
                        except sqlite3.IntegrityError:
                            st.error("❌ Essa placa já está cadastrada no sistema.")
                    else:
                        st.warning("Preencha a Placa e o Modelo para continuar.")
                        
        with tab_mot:
            st.subheader("Inserir Novo Motorista no Prontuário")
            with st.form("form_cadastro_motorista", clear_on_submit=True):
                nome_m = st.text_input("Nome Completo do Condutor")
                # Campos solicitados para CNH e vencimento
                cnh_m = st.text_input("Número da CNH")
                venc_cnh = st.date_input("Data de Vencimento da CNH")
                
                # Campo solicitado para o Termo de Utilização
                st.write("---")
                st.caption("📜 Termo de Responsabilidade e Utilização de Veículo Corporativo")
                st.info("O condutor abaixo declara estar ciente das regras de trânsito, zelo pelo patrimônio da empresa, conformidade com os apontamentos de checklist de campo e aplicação de penalidades em caso de sinistros culposos.")
                aceitou_termo = st.checkbox("O motorista leu e concorda expressamente com o Termo de Utilização acima")
                
                cadastrar_m = st.form_submit_button("Salvar Motorista na Base")
                if cadastrar_m:
                    if nome_m and cnh_m:
                        if aceitou_termo:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO motoristas VALUES (?, ?, ?, 'Sim')", (nome_m, cnh_m, str(venc_cnh)))
                            conn.commit()
                            st.success(f"👤 Condutor {nome_m} cadastrado com CNH e Termo de Utilização validados!")
                        else:
                            st.error("❌ Não é possível cadastrar sem dar o aceite no Termo de Utilização.")
                    else:
                        st.warning("Preencha o Nome e a CNH do motorista.")

    # ==========================================
    # 4. MÓDULO: CHECKLIST DE CAMPO
    # ==========================================
    elif escolha == "📋 Checklist de Campo":
        st.title("📋 Checklist Prático de Entrada e Saída")
        st.caption("Foco operacional: Interface rápida adaptada para celulares e tablets de campo.")
        
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        with st.form("form_checklist", clear_on_submit=True):
            placa = st.selectbox("Selecione a Placa do Veículo", df_veiculos['placa'])
            tipo = st.selectbox("Tipo de Movimentação", ["Entrada de Oficina", "Saída de Oficina", "Novo Contrato", "Devolução", "Substituição"])
            km = st.number_input("Quilometragem (KM) Atual", min_value=0, step=1)
            combustivel = st.selectbox("Nível do Tanque", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
            pneus = st.radio("Condição dos Pneus (Sulco)", ["Ok (Acima de 1.6mm)", "Alerta (Careca / Troca Necessária)"])
            avarias = st.text_input("Descreva avarias, sinistros ou observações gerais")
            operador = st.text_input("Nome do Operador de Campo")
            
            enviar = st.form_submit_button("Transmitir Checklist em Tempo Real")
            
            if enviar:
                cursor = conn.cursor()
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                cursor.execute("INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) VALUES (?,?,?,?,?,?,?,?)",
                               (placa, tipo, km, combustivel, avarias, pneus, operador, data_atual))
                cursor.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (km, placa))
                conn.commit()
                st.success(f"✅ Checklist de {tipo} enviado! Dados consolidados na base do Gestor.")

    # ==========================================
    # 5. MÓDULO: ABASTECIMENTO
    # ==========================================
    elif escolha == "⛽ Abastecimento":
        st.title("⛽ Lançamento de Abastecimento / Cartão Combustível")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        with st.form("form_abastecimento", clear_on_submit=True):
            placa = st.selectbox("Veículo", df_veiculos['placa'])
            valor = st.number_input("Valor Total Pago (R$)", min_value=0.0, step=10.0)
            km = st.number_input("KM registrado no ato", min_value=0)
            
            salvar = st.form_submit_button("Registrar Abastecimento")
            if salvar:
                cursor = conn.cursor()
                data_atual = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", (placa, valor, data_atual))
                cursor.execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (km, placa))
                conn.commit()
                st.success("⛽ Gasto computado com sucesso no fluxo financeiro corporativo!")

    # ==========================================
    # 6. MÓDULO: OS & APROVAÇÕES
    # ==========================================
    elif escolha == "🛠️ OS & Aprovações":
        st.title("🛠️ Fluxo Central de Ordens de Serviço e Manutenções")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        tab1, tab2 = st.tabs(["Abrir Nova OS", "Fila de Aprovações Técnicas"])
        
        with tab1:
            with st.form("form_os"):
                placa = st.selectbox("Selecione o Veículo", df_veiculos['placa'])
                tipo_m = st.selectbox("Tipo de Manutenção", ["Preventiva (Revisão/Troca de Óleo)", "Corretiva"])
                desc = st.text_area("Descreva o problema/serviço")
                custo = st.number_input("Custo Previsto (R$)", min_value=0.0)
                
                criar = st.form_submit_button("Gerar Ordem de Serviço")
                if criar:
                    cursor = conn.cursor()
                    data_atual = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO ordens_servico (placa, tipo, descricao, custo, data) VALUES (?,?,?,?,?)", (placa, tipo_m, desc, custo, data_atual))
                    cursor.execute("UPDATE veiculos SET status = 'Em Manutenção' WHERE placa = ?", (placa,))
                    conn.commit()
                    st.warning(f"⚠️ OS Gerada! Veículo {placa} foi bloqueado com o status 'Em Manutenção'.")
                    st.rerun()
                    
        with tab2:
            st.write("### Aprovações de Manutenção pendentes:")
            df_os = pd.read_sql_query("SELECT * FROM ordens_servico WHERE status != 'Encerrado'", conn)
            
            if df_os.empty:
                st.info("Nenhuma OS pendente de fluxo no momento.")
            else:
                for idx, row in df_os.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**OS #{row['id']}** - {row['placa']} | {row['tipo']} | Custo: R$ {row['custo']} | **Status: {row['status']}**")
                    
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
                            cursor.execute("UPDATE ordens_servico SET status = 'Encerrado' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE veiculos SET status = 'Disponível' WHERE placa = ?", (row['placa'],))
                            cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Manutenção', ?, ?)", (row['placa'], row['custo'], row['data']))
                            conn.commit()
                            st.success("Veículo liberado para a rota!")
                            st.rerun()

    # ==========================================
    # 7. MÓDULO: MULTAS AUTOMATIZADAS
    # ==========================================
    elif escolha == "⚠️ Multas Automatizadas":
        st.title("⚠️ Lançamento Inteligente de Infrações")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        col1, col2 = st.columns(2)
        with col1:
            placa = st.selectbox("Veículo Infrator", df_veiculos['placa'])
            data_m = st.text_input("Data da Infração (DD/MM/AAAA)")
            endereco = st.text_input("Endereço / Rodovia do Flagrante")
            codigo = st.text_input("Código de Infração (Ex: 7455-0, 7463-0, 5010-0)")
            
            calcular = st.button("Processar e Autopreencher Dados")
            
        with col2:
            if calcular:
                if codigo in DICIONARIO_MULTAS:
                    info = DICIONARIO_MULTAS[codigo]
                    st.subheader("Dados Calculados Automatizados:")
                    st.write(f"**Gravidade:** {info['gravidade']}")
                    st.write(f"**Pontuação:** {info['pontos']} pontos")
                    st.write(f"**Valor Legal:** R$ {info['valor']}")
                    st.info(f"**Descrição:** {info['desc']}")
                    
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO multas (placa, data, endereco, codigo, gravidade, pontos, valor, descricao) VALUES (?,?,?,?,?,?,?,?)",
                                   (placa, data_m, endereco, codigo, info['gravidade'], info['pontos'], info['valor'], info['desc']))
                    cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Multa', ?, ?)", (placa, info['valor'], data_m))
                    conn.commit()
                    st.success("🚨 Infração vinculada e provisionada no custo operacional!")

    # ==========================================
    # 8. MÓDULO: CONTRATOS, PEDÁGIOS E SINISTROS
    # ==========================================
    elif escolha == "📝 Gestão de Contratos & Sinistros":
        st.title("📝 Lançamentos Administrativos Gerais")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        tipo_c = st.selectbox("Tipo de Lançamento", ["Pedágio (Tag/Eixos)", "Sinistro (Batidas/Franquias)", "Novo Contrato / Locação / Substituição"])
        
        with st.form("form_admin"):
            placa = st.selectbox("Veículo Vinculado", df_veiculos['placa'])
            valor = st.number_input("Custo Financeiro (R$)", min_value=0.0)
            obs = st.text_area("Notas / Detalhes")
            
            salvar_adm = st.form_submit_button("Computar no Custo de Operação")
            if salvar_adm:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, ?, ?, ?)", (placa, tipo_c, valor, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"Sucesso! Custo de {tipo_c} integrado com sucesso.")

    # ==========================================
    # 9. MÓDULO: DASHBOARD, KPIS E ALERTAS
    # ==========================================
    elif escolha == "📊 Dashboard & KPIs":
        st.title("📊 Painel Executivo e Tomada de Decisão")
        
        st.subheader("⚠️ Central de Alertas Preditivos (Manutenção 10k KM e CNH)")
        col_al1, col_al2 = st.columns(2)
        
        with col_al1:
            df_km = pd.read_sql_query("SELECT placa, km_atual, km_proxima_revisao FROM veiculos", conn)
            for _, r in df_km.iterrows():
                dif = r['km_proxima_revisao'] - r['km_atual']
                if dif <= 1500:
                    st.error(f"🚨 REVISÃO URGENTE: Veículo {r['placa']} está com {r['km_atual']} KM. Próxima revisão obrigatória em {r['km_proxima_revisao']} KM (Faltam {dif} KM!)")
        
        with col_al2:
            df_mot = pd.read_sql_query("SELECT * FROM motoristas", conn)
            for _, r in df_mot.iterrows():
                venc = datetime.strptime(r['cnh_vencimento'], "%Y-%m-%d")
                if venc <= datetime.now() + timedelta(days=60):
                    st.warning(f"⚠️ CNH Próxima do Vencimento: Condutor {r['nome']} vence em {venc.strftime('%d/%m/%Y')}")

        st.divider()

        df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
        total_geral = df_fin['valor'].sum() if not df_fin.empty else 0.0
        c_comb = df_fin[df_fin['tipo_custo'] == 'Combustível']['valor'].sum()
        c_man = df_fin[df_fin['tipo_custo'] == 'Manutenção']['valor'].sum()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Custo Total de Operação", f"R$ {total_geral:,.2f}")
        kpi2.metric("Total Cartão Combustível", f"R$ {c_comb:,.2f}")
        kpi3.metric("Investimento em Oficinas", f"R$ {c_man:,.2f}")
        
        st.divider()
        
        st.subheader("📈 Gráfico de Distribuição Real de Custos")
        if not df_fin.empty:
            grafico_data = df_fin.groupby('tipo_custo')['valor'].sum().reset_index()
            chart = alt.Chart(grafico_data).mark_bar(color='#1f6aa5').encode(
                x=alt.X('tipo_custo:N', title='Natureza do Custo'),
                y=alt.Y('valor:Q', title='Total Acumulado (R$)')
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aguardando lançamentos financeiros para gerar os gráficos.")
            
        st.divider()

        st.subheader("📥 Exportação de Relatórios Gerenciais")
        tab_rel1, tab_rel2 = st.tabs(["Checklists de Campo Efetuados", "Extrato Financeiro Completo"])
        
        with tab_rel1:
            df_chk_rep = pd.read_sql_query("SELECT * FROM checklists", conn)
            st.dataframe(df_chk_rep, use_container_width=True)
            st.download_button("Exportar Planilha de Checklists (CSV)", df_chk_rep.to_csv(index=False), "relatorio_checklists.csv", "text/csv")
            
        with tab_rel2:
            st.dataframe(df_fin, use_container_width=True)
            st.download_button("Exportar Planilha Financeira (CSV)", df_fin.to_csv(index=False), "extrato_financeiro.csv", "text/csv")
