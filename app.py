import streamlit as st
import sqlite3
import pandas as pd

# Configuração global
st.set_page_config(page_title="SGF-Pro V16", layout="wide")

# Inicialização do Banco de Dados
def init_db():
    conn = sqlite3.connect('frotas_v16.db', check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    conn.commit()
    return conn

conn = init_db()

# Função principal que "desenha" o sistema
def main():
    st.title("🚗 Sistema de Gestão de Frotas SGF-Pro")
    
    # Menu lateral
    menu = st.sidebar.radio("Navegação", ["Home", "🚗 Veículos"])
    
    if menu == "Home":
        st.write("### Bem-vindo ao Sistema!")
        st.write("Se consegue ler esta mensagem, o código está a rodar corretamente.")
    
    elif menu == "🚗 Veículos":
        st.header("Gestão de Veículos")
        with st.form("form_veic"):
            placa = st.text_input("Placa")
            modelo = st.text_input("Modelo")
            if st.form_submit_button("Salvar"):
                conn.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?)", (placa, modelo))
                conn.commit()
                st.success("Veículo salvo!")
        
        # Mostrar o que está no banco
        df = pd.read_sql("SELECT * FROM veiculos", conn)
        st.dataframe(df)

# Execução obrigatória
if __name__ == "__main__":
    main()
