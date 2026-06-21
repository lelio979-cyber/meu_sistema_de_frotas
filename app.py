import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DICIONÁRIO DE MULTAS (Banco de Conhecimento) ---
DICIONARIO_MULTAS = {
    "501-1": {"desc": "Excesso de velocidade > 50%", "valor": 880.41, "pontos": 7, "gravidade": "Gravíssima"},
    "602-0": {"desc": "Conduzir sem cinto de segurança", "valor": 195.23, "pontos": 5, "gravidade": "Grave"},
    "518-5": {"desc": "Estacionar em local proibido", "valor": 130.16, "pontos": 4, "gravidade": "Média"}
}

# --- CONFIGURAÇÃO E BANCO ---
conn = sqlite3.connect("sgf_erp_pro.db", check_same_thread=False)

# Criar tabelas com relacionamento de status
conn.execute("""CREATE TABLE IF NOT EXISTS frota 
    (id INTEGER PRIMARY KEY, placa TEXT, modelo TEXT, status TEXT DEFAULT 'Disponível')""")
conn.execute("""CREATE TABLE IF NOT EXISTS multas 
    (id INTEGER PRIMARY KEY, id_veiculo INTEGER, codigo_multa TEXT, local TEXT, data TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS sinistros 
    (id INTEGER PRIMARY KEY, id_veiculo INTEGER, local TEXT, feridos INTEGER, terceiro INTEGER, detalhes TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS aprovacoes 
    (id INTEGER PRIMARY KEY, id_referencia INTEGER, tipo_referencia TEXT, aprovador TEXT, data TEXT)""")
conn.commit()

# --- LÓGICA DE INTEGRAÇÃO (A "Engrenagem") ---
def atualizar_status_veiculo(id_veiculo, novo_status):
    conn.execute("UPDATE frota SET status = ? WHERE id = ?", (novo_status, id_veiculo))
    conn.commit()

# --- INTERFACE ---
st.set_page_config(layout="wide")
menu = st.sidebar.radio("Módulos", ["Dashboard", "Multas", "Sinistros", "Ordens de Serviço", "Checklist/Status", "Aprovações"])

if menu == "Checklist/Status":
    st.title("✅ Checklist e Status Operacional")
    with st.form("f_check"):
        id_v = st.number_input("ID Veículo")
        novo_status = st.selectbox("Status para o veículo", ["Disponível", "Em Manutenção", "Sinistrado", "Em Viagem"])
        if st.form_submit_button("Atualizar e Aplicar ao Sistema"):
            atualizar_status_veiculo(id_v, novo_status)
            st.success(f"Status do veículo {id_v} alterado para {novo_status} em todo o sistema!")

elif menu == "Multas":
    st.title("🚔 Registro de Multas")
    
    cod_selecionado = st.selectbox("Código da Multa", list(DICIONARIO_MULTAS.keys()))
    info = DICIONARIO_MULTAS[cod_selecionado]
    
    # Exibir detalhes automaticamente
    st.info(f"**Infração:** {info['desc']} | **Valor:** R$ {info['valor']} | **Pontos:** {info['pontos']}")
    
    id_v = st.number_input("ID Veículo")
    local = st.text_input("Local da Infração")
    
    if st.button("Lançar Multa"):
        conn.execute("INSERT INTO multas (id_veiculo, codigo_multa, local, data) VALUES (?,?,?,?)", 
                     (id_v, cod_selecionado, local, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        st.success("Multa vinculada!")

elif menu == "Aprovações":
    st.title("✅ Centro de Aprovações")
    ref_id = st.number_input("ID da OS ou Checklist")
    tipo = st.selectbox("Tipo", ["OS", "Checklist"])
    nome = st.text_input("Nome do Aprovador")
    if st.button("Aprovar"):
        conn.execute("INSERT INTO aprovacoes (id_referencia, tipo_referencia, aprovador, data) VALUES (?,?,?,?)", 
                     (ref_id, tipo, nome, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        # Se for OS, muda status para Manutenção
        if tipo == "OS": atualizar_status_veiculo(ref_id, "Em Manutenção")
        st.success("Aprovado e status atualizado!")

elif menu == "Sinistros":
    st.title("💥 Registro de Sinistros")
    with st.form("f_sinistro"):
        id_v = st.number_input("ID Veículo")
        feridos = st.checkbox("Houve Feridos?")
        terceiro = st.checkbox("Causado por Terceiros?")
        detalhes = st.text_area("Detalhes do Ocorrido")
        if st.form_submit_button("Salvar Sinistro"):
            conn.execute("INSERT INTO sinistros (id_veiculo, feridos, terceiro, detalhes) VALUES (?,?,?,?)", 
                         (id_v, int(feridos), int(terceiro), detalhes))
            atualizar_status_veiculo(id_v, "Sinistrado")
            conn.commit()
            st.success("Sinistro registrado e veículo marcado como Sinistrado.")

# --- TABELAS DINÂMICAS ---
st.divider()
st.subheader("Visualização Dinâmica")
tab_select = st.selectbox("Qual tabela deseja consultar?", ["Frota", "Multas", "Sinistros"])
st.dataframe(pd.read_sql(f"SELECT * FROM {tab_select.lower().replace('frota', 'frota')}", conn), use_container_width=True)
