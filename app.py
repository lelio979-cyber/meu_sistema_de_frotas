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
    
    # Veículos
    cursor.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', 
        km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base Central', tipo_frota TEXT)''')
    
    # Checklists (Foco Operacional)
    cursor.execute('''CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, 
        combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)''')
    
    # Ordens de Serviço (OS)
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, 
        custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT)''')
    
    # Financeiro Integral
    cursor.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)''')
    
    # Multas
    cursor.execute('''CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, data TEXT, endereco TEXT, 
        codigo TEXT, gravidade TEXT, pontos INTEGER, valor REAL, descricao TEXT)''')

    # CNHs
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        nome TEXT PRIMARY KEY, cnh_vencimento TEXT)''')
    
    # Inserções Iniciais para Testes se vazio
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO veiculos VALUES ('BRA2E19', 'Volvo FH 540', 92000, 'Disponível', 100000, 'Rota SP-RJ', 'Próprio')")
        cursor.execute("INSERT INTO veiculos VALUES ('ABC1234', 'Scania R450', 149500, 'Disponível', 150000, 'Rota SP-BH', 'Reserva')")
        cursor.execute("INSERT INTO motoristas VALUES ('João Silva', '2026-05-10')")
        cursor.execute("INSERT INTO motoristas VALUES ('Carlos Souza', '2026-08-20')")
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
        opcoes_menu = ["📊 Dashboard & KPIs", "🚗 Cadastrar Veículo", "📋 Checklist de Campo", "⛽ Abastecimento", "🛠️ OS & Aprovações", "⚠️ Multas Automatizadas", "📝 Gestão de Contratos & Sinistros"]
        
    escolha = st.sidebar.radio("Navegação:", opcoes_menu)
    
    if st.sidebar.button("🚪 Sair do Sistema", type="primary"):
        st.session_state['autenticado'] = False
        st.session_state['perfil'] = None
        st.rerun()

    # ==========================================
    # MÓDULO NOVO: CADASTRO DE VEÍCULO (GESTOR)
    # ==========================================
    if escolha == "🚗 Cadastrar Veículo":
        st.title("🚗 Cadastro Central de Veículos da Frota")
        st.caption("Adicione novos veículos próprios, alugados ou reservas para liberar no checklist de campo.")
        
        with st.form("form_cadastro_veiculo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nova_placa = st.text_input("Placa do Veículo (Ex: ABC1234 / BRA2E19)").upper().strip()
                novo_modelo = st.text_input("Modelo / Marca (Ex: Volvo FH 540)")
                km_inicial = st.number_input("Quilometragem (KM) Atual", min_value=0, step=1)
            with col2:
                tipo_frota = st.selectbox("Categoria da Frota", ["Próprio", "Alugado", "Reserva"])
                trecho_inicial = st.text_input("Trecho / Rota de Operação Atual", value="Base Central")
                plano_revisao = st.selectbox("Plano de Revisão Preventiva (Troca de Óleo)", [10000, 15000, 20000], help="De quantos em quantos KMs este veículo deve revisar?")
            
            cadastrar = st.form_submit_button("Salvar Veículo na Base de Dados")
            
            if cadastrar:
                if not nova_placa or not novo_modelo:
                    st.error("❌ Por favor, preencha a placa e o modelo do veículo.")
                else:
                    try:
                        cursor = conn.cursor()
                        # Calcula a km da próxima revisão somando o plano escolhido à km atual
                        proxima_rev = km_inicial + plano_revisao
                        
                        cursor.execute("INSERT INTO veiculos (placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota) VALUES (?, ?, ?, 'Disponível', ?, ?, ?)",
                                       (nova_placa, novo_modelo, km_inicial, proxima_rev, trecho_inicial, tipo_frota))
                        conn.commit()
                        st.success(f"✅ Veículo {nova_placa} ({novo_modelo}) cadastrado com sucesso! Já está disponível para os operadores de campo.")
                    except sqlite3.IntegrityError:
                        st.error("❌ Erro: Já existe um veículo cadastrado com esta mesma placa.")

        # Exibe os veículos já cadastrados logo abaixo
        st.write("### Frota Ativa Cadastrada")
        df_ativos = pd.read_sql_query("SELECT placa, modelo, km_atual, km_proxima_revisao, status, trecho, tipo_frota FROM veiculos", conn)
        st.dataframe(df_ativos, use_container_width=True)

    # ==========================================
    # 3. MÓDULO 1: CHECKLIST DE CAMPO
    # ==========================================
    elif escolha == "📋 Checklist de Campo":
        st.title("📋 Checklist Prático de Entrada e Saída")
        st.caption("Foco operacional: Interface rápida adaptada para celulares e tablets de campo.")
        
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        if df_veiculos.empty:
            st.warning("⚠️ Nenhum veículo cadastrado na base. O gestor precisa cadastrar um veículo primeiro.")
        else:
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
    # 4. MÓDULO 2: ABASTECIMENTO
    # ==========================================
    elif escolha == "⛽ Abastecimento":
        st.title("⛽ Lançamento de Abastecimento / Cartão Combustível")
        df_veiculos = pd.read_sql_query("SELECT placa FROM veiculos", conn)
        
        if df_veiculos.empty:
            st.warning("⚠️ Nenhum veículo cadastrado na base.")
        else:
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
    # 5. MÓDULO 3: OS & APROVAÇÕES
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
                    col1.write(f"**OS #{row['id']}** - {row['placa']} | {row['tipo']} | Custo: R$ {row['custo']} | **Status Atual: {row['status']}**")
                    
                    if row['status'] == 'Aguardando Aprovação':
                        if col2.button("✔️ Aprovar (Iniciar)", key=f"ap_{row['id']}"):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE ordens_servico SET status = 'Em Andamento' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE veiculos SET status = 'Em Andamento' WHERE placa = ?", (row['placa'],))
                            conn.commit()
                            st.rerun()
                    elif row['status'] == 'Em Andamento':
                        if col3.button("🔒 Encerrar (Liberar)", key=f"en_{row['id']}"):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE ordens_servico SET status = 'Encerrado' WHERE id = ?", (row['id'],))
                            cursor.execute("UPDATE veiculos SET status = 'Disponível' WHERE placa = ?", (row['placa'],))
                            cursor.execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Manutenção', ?, ?)", (row['placa'], row['custo'], row['data']))
                            conn.commit()
                            st.success("Veículo liberado para a rota!")
                            st.rerun()

    # =================
