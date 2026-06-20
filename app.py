import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import base64

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SGF-Fleet Pro", layout="wide")
DB_NAME = "sgf_fleet_v3.db"

# Função para gerar o PDF da OS
def gerar_pdf(placa, servico, custo, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="ORDEM DE SERVIÇO - SGF-Fleet", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Veiculo: {placa}", ln=True)
    pdf.cell(200, 10, txt=f"Servico: {servico}", ln=True)
    pdf.cell(200, 10, txt=f"Custo: R$ {custo:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Data: {data}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- MÓDULO DE GESTÃO ---
def abrir_os():
    st.title("🛠️ Emitir Ordem de Serviço")
    conn = sqlite3.connect(DB_NAME)
    veiculos = pd.read_sql("SELECT placa FROM veiculos", conn)['placa'].tolist()
    
    with st.form("form_pdf"):
        placa = st.selectbox("Veículo", veiculos)
        servico = st.text_input("Descrição do Serviço")
        custo = st.number_input("Custo (R$)", min_value=0.0)
        data = st.date_input("Data")
        
        if st.form_submit_button("Gerar e Salvar OS"):
            # Salva no Banco
            conn.execute("INSERT INTO os (placa, servico, custo, data) VALUES (?,?,?,?)", 
                         (placa, servico, custo, data))
            conn.commit()
            
            # Gera o PDF para Download
            pdf_data = gerar_pdf(placa, servico, custo, str(data))
            st.download_button(label="📥 Baixar PDF da OS", data=pdf_data, 
                               file_name=f"OS_{placa}_{data}.pdf", mime="application/pdf")
            st.success("OS gerada com sucesso!")
    conn.close()

# --- DASHBOARD DE GESTÃO ---
def dashboard():
    st.title("📊 Painel de Controle Corporativo")
    conn = sqlite3.connect(DB_NAME)
    df_os = pd.read_sql("SELECT * FROM os", conn)
    conn.close()
    
    st.subheader("Custos de Manutenção por Veículo")
    if not df_os.empty:
        fig = pd.pivot_table(df_os, values='custo', index='placa', aggfunc='sum')
        st.bar_chart(fig)
        st.dataframe(df_os, use_container_width=True)

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Frota", "Emitir OS"])
if menu == "Dashboard": dashboard()
elif menu == "Emitir OS": abrir_os()
