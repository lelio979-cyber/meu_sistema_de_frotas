import streamlit as st
import sqlite3
import pandas as pd

def get_db():
    return sqlite3.connect('frotas_limpo.db', check_same_thread=False)

def init_tables():
    conn = get_db()
    # Adicionando campos essenciais para uma gestão profissional
    conn.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY, 
            modelo TEXT,
            marca TEXT,
            ano INTEGER,
            chassi TEXT,
            renavam TEXT,
            data_aquisicao DATE,
            km_atual INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_tables()

def main():
    st.set_page_config(page_title="SGF-Pro Elite", layout="wide")
    st.title("🚗 Cadastro Técnico de Frota")
    
    with st.form("form_veiculo_completo", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            placa = st.text_input("Placa").upper()
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
        with col2:
            ano = st.number_input("Ano Fabricação", 1990, 2030)
            chassi = st.text_input("Chassi")
            renavam = st.text_input("Renavam")
        with col3:
            data_aq = st.date_input("Data de Aquisição")
            km = st.number_input("KM Atual", min_value=0)
            status = st.selectbox("Status", ["Ativo", "Inativo", "Manutenção", "Vendido"])
        
        if st.form_submit_button("Salvar Veículo no Banco"):
            try:
                conn = get_db()
                conn.execute("""
                    INSERT INTO veiculos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (placa, modelo, marca, ano, chassi, renavam, data_aq, km, status))
                conn.commit()
                conn.close()
                st.success("Veículo cadastrado com especificações técnicas!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    # Exibição Técnica
    st.subheader("Frota Ativa")
    conn = get_db()

    import streamlit as st
import sqlite3
import pandas as pd
import os

# Configuração de pastas
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():
    return sqlite3.connect('frotas_elite.db', check_same_thread=False)

# Função para Salvar Arquivo
def save_uploaded_file(uploaded_file, placa):
    file_path = os.path.join(UPLOAD_FOLDER, f"{placa}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def main():
    st.title("🚗 Cadastro Técnico de Frota v24")
    
    # --- FORMULÁRIO DE CADASTRO ---
    with st.expander("➕ Adicionar Novo Veículo"):
        with st.form("form_novo"):
            c1, c2 = st.columns(2)
            placa = c1.text_input("Placa").upper()
            modelo = c2.text_input("Modelo")
            foto = st.file_uploader("Foto do Veículo", type=['jpg', 'png'])
            doc = st.file_uploader("Documento (PDF/Doc)", type=['pdf', 'docx'])
            
            if st.form_submit_button("Salvar Registro"):
                path_foto = save_uploaded_file(foto, placa) if foto else None
                path_doc = save_uploaded_file(doc, placa) if doc else None
                
                conn = get_db()
                conn.execute("INSERT INTO veiculos (placa, modelo, foto, doc) VALUES (?,?,?,?)", 
                             (placa, modelo, path_foto, path_doc))
                conn.commit()
                conn.close()
                st.success("Veículo salvo!")

    # --- GESTÃO DA FROTA (EDITAR/EXCLUIR) ---
    st.subheader("Frota Ativa")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    
    for i, row in df.iterrows():
        cols = st.columns([3, 1, 1])
        cols[0].write(f"**{row['placa']}** - {row['modelo']}")
        
        if cols[1].button("✏️ Editar", key=f"edit_{row['placa']}"):
            st.session_state['edit_placa'] = row['placa']
            
        if cols[2].button("🗑️ Excluir", key=f"del_{row['placa']}"):
            conn.execute("DELETE FROM veiculos WHERE placa = ?", (row['placa'],))
            conn.commit()
            st.rerun()
            
    conn.close()

if __name__ == "__main__":
    main()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()

if __name__ == "__main__":
    main()
