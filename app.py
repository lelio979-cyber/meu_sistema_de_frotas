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
# 2. MENU LATERAL (CARREGAMENTO DIRETO)
# ==========================================
st.sidebar.title("FleetX Control")
st.sidebar.write("**Perfil ativo:** GESTOR (Modo Completo)")

opcoes_menu = [
    "📊 Dashboard & KPIs", 
    "🚗 Cadastros Gerais (Frota/Motoristas)", 
    "📍 Atualização de KM Diária",
    "📋 Checklist de Campo", 
    "⛽ Abastecimento", 
    "🛠️ OS & Aprovações", 
    "⚠️ Multas Automatizadas", 
    "📝 Gestão de Contratos & Sinistros"
]
    
escolha = st.sidebar.radio("Navegação:", opcoes_menu)

# ==========================================
# 3. MÓDULO: DASHBOARD & KPIS
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
            venc = datetime.strptime(r['cnh_vencimento'], "%Y-%m-%d")
            if venc <= datetime.now() + timedelta(days=60):
                st.warning(f"CNH Próxima do Vencimento: Condutor {r['nome']} vence em {venc.strftime('%d/%m/%Y')}")

    st.divider()

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

# ==========================================
# 4. MÓDULO: CADASTROS GERAIS
# ==========================================
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
        with st.form("form_cadastro_motorista", clear_on_submit
