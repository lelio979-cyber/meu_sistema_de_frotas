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
