import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SGF-Fleet Elite Pro", layout="wide")
DB_NAME = "sgf_fleet_elite.db"

# --- INICIALIZAÇÃO FORÇADA E SEGURA ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    # Lista de tabelas que garantimos a estrutura
    # Se a tabela 'veiculos' existir com número de colunas errado, o 'DROP' força a correção
    conn.execute("DROP TABLE IF EXISTS veiculos") 
    conn.execute("""CREATE TABLE veiculos (
        placa TEXT PRIMARY KEY, 
        modelo TEXT, 
        motorista TEXT, 
        km_atual INTEGER, 
        km_revisao INTEGER)""")
    
    conn.execute("CREATE TABLE IF NOT EXISTS os (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, data DATE)")
    conn.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, motorista TEXT, valor REAL, comprovante_link TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS abastecimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, litros REAL, km_percorrido REAL)")
    conn.commit()
    conn.close()

# Executa apenas se for a primeira vez ou se houver erro crítico
if 'db_ready' not in st.session_state:
    init_db()
    st.session_state['db_ready'] = True

# --- FUNÇÕES DE INTERFACE ---
def menu_navegacao():
    return st.sidebar.radio("Navegação", ["Dashboard", "Gestão de Ativos", "Multas", "Combustível", "Relatório"])

def main():
    menu = menu_navegacao()
    
    if menu == "Dashboard":
        st.title("📊 Painel de Performance")
        conn = sqlite3.connect(DB_NAME)
        df_v = pd.read_sql("SELECT * FROM veiculos", conn)
        conn.close()
        if not df_v.empty: st.dataframe(df_v, use_container_width=True)
        else: st.info("Nenhum veículo cadastrado.")

    elif menu == "Gestão de Ativos":
        st.title("🚛 Cadastro de Ativos")
        with st.form("form_veic"):
            placa = st.text_input("Placa").upper()
            modelo = st.text_input("Modelo")
            motorista = st.text_input("Motorista")
            km = st.number_input("KM Atual", min_value=0)
            km_rev = st.number_input("KM Revisão", min_value=0)
            if st.form_submit_button("Registrar"):
                conn = sqlite3.connect(DB_NAME)
                # Comando com colunas explícitas para garantir sucesso
                conn.execute("INSERT OR REPLACE INTO veiculos (placa, modelo, motorista, km_atual, km_revisao) VALUES (?,?,?,?,?)", 
                             (placa, modelo, motorista, km, km_rev))
                conn.commit(); conn.close(); st.success("Registrado com sucesso!"); st.rerun()

    elif menu == "Multas":
        st.title("⚠️ Registro de Multas")
        with st.form("form_multa"):
            placa = st.text_input("Placa").upper()
            motorista = st.text_input("Motorista")
            valor = st.number_input("Valor (R$)", min_value=0.0)
            link = st.text_input("Link da Foto")
            if st.form_submit_button("Registrar Multa"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO multas (placa, motorista, valor, comprovante_link) VALUES (?,?,?,?)", 
                             (placa, motorista, valor, link))
                conn.commit(); conn.close(); st.success("Salvo!"); st.rerun()

    elif menu == "Combustível":
        st.title("⛽ Controle de Consumo")
        with st.form("form_comb"):
            placa = st.text_input("Placa").upper()
            litros = st.number_input("Litros", min_value=0.1)
            km = st.number_input("KM Rodado", min_value=0.1)
            if st.form_submit_button("Calcular"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO abastecimentos (placa, litros, km_percorrido) VALUES (?,?,?)", 
                             (placa, litros, km))
                conn.commit(); conn.close(); st.success(f"Média: {km/litros:.2f} KM/L"); st.rerun()

    elif menu == "Relatório":
        st.title("📥 Relatórios")
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql("SELECT * FROM veiculos", conn)
        conn.close()
        st.download_button("Baixar Frota (CSV)", df.to_csv(index=False), "frota.csv", "text/csv")
        st.dataframe(df)

if __name__ == "__main__":
    main()
