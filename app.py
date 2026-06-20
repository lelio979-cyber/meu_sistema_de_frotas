import streamlit as st
import sqlite3
import pandas as pd

def get_db():
    return sqlite3.connect('frotas_elite.db', check_same_thread=False)

def main():
    st.title("🚗 Gestão Técnica de Frota v25")
    
    # --- LÓGICA DE EDIÇÃO ---
    if 'edit_placa' in st.session_state:
        placa_edicao = st.session_state['edit_placa']
        st.subheader(f"Editando Veículo: {placa_edicao}")
        
        # Carrega dados atuais
        conn = get_db()
        veiculo = conn.execute("SELECT * FROM veiculos WHERE placa = ?", (placa_edicao,)).fetchone()
        conn.close()
        
        with st.form("form_edicao"):
            novo_modelo = st.text_input("Modelo", value=veiculo[1]) # Index baseado na tabela
            
            if st.form_submit_button("Atualizar Registro"):
                conn = get_db()
                conn.execute("UPDATE veiculos SET modelo = ? WHERE placa = ?", (novo_modelo, placa_edicao))
                conn.commit()
                conn.close()
                del st.session_state['edit_placa'] # Fecha modo edição
                st.rerun()
            
            if st.form_submit_button("Cancelar"):
                del st.session_state['edit_placa']
                st.rerun()

    # --- LISTAGEM E EXCLUSÃO (Mantido) ---
    st.subheader("Frota Ativa")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM veiculos", conn)
    conn.close()

    for i, row in df.iterrows():
        cols = st.columns([4, 1, 1])
        cols[0].write(f"**{row['placa']}** - {row['modelo']}")
        
        if cols[1].button("✏️ Editar", key=f"edit_{row['placa']}"):
            st.session_state['edit_placa'] = row['placa']
            st.rerun()
            
        if cols[2].button("🗑️ Excluir", key=f"del_{row['placa']}"):
            conn = get_db()
            conn.execute("DELETE FROM veiculos WHERE placa = ?", (row['placa'],))
            conn.commit()
            conn.close()
            st.rerun()

if __name__ == "__main__":
    main()
