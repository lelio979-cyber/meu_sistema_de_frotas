import streamlit as st
import sqlite3
import pandas as pd

# Conexão baseada na versão anterior
def get_db():
    return sqlite3.connect('frotas_limpo.db', check_same_thread=False)

def init_tables():
    conn = get_db()
    # Apaga a tabela se ela existir, para garantir que as colunas fiquem certas
    conn.execute("DROP TABLE IF EXISTS veiculos")
    conn.execute("""
        CREATE TABLE veiculos (
            placa TEXT PRIMARY KEY, 
            modelo TEXT,
            ano INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_tables()

def main():
    st.title("SGF-Pro V22 | Gestão de Veículos")
    
    # Navegação
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro de Veículos"])
    
    if menu == "Dashboard":
        st.write("Bem-vindo ao sistema.")
        
    elif menu == "Cadastro de Veículos":
        st.subheader("Cadastrar Novo Veículo")
        
        # Formulário Profissional
        with st.form("form_veiculo", clear_on_submit=True):
            placa = st.text_input("Placa do Veículo (Ex: ABC-1234)").upper()
            modelo = st.text_input("Modelo")
            ano = st.number_input("Ano", min_value=1990, max_value=2030, step=1)
            
            submit = st.form_submit_button("Salvar Veículo")
            
            if submit:
                if placa:
                    conn = get_db()
                    try:
                        conn.execute("INSERT INTO veiculos (placa, modelo, ano) VALUES (?, ?, ?)", (placa, modelo, ano))
                        conn.commit()
                        st.success(f"Veículo {placa} cadastrado com sucesso!")
                    except sqlite3.IntegrityError:
                        st.error("Erro: Esta placa já existe no sistema.")
                    conn.close()
                else:
                    st.warning("A placa é obrigatória.")

        # Exibição dos dados
        st.subheader("Veículos Cadastrados")
        conn = get_db()
        df = pd.read_sql("SELECT * FROM veiculos", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

if __name__ == "__main__":
    main()
