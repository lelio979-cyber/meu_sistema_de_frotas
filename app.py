import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

st.set_page_config(page_title="FleetX", layout="wide")

def ger_hash(s): 
    return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS usuarios "
              "(usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS veiculos "
              "(placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, "
              "status TEXT DEFAULT 'Disponível', km_proxima_revisao INTEGER, "
              "trecho TEXT, tipo_frota TEXT, documento TEXT, arquivo_crlv BLOB, "
              "locadora_nome TEXT, data_locacao TEXT, data_devolucao TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS motoristas "
              "(nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, "
              "termo_aceite TEXT, arquivo_cnh BLOB, arquivo_termo BLOB)")
    c.execute("CREATE TABLE IF NOT EXISTS checklists "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, "
              "tipo_movimentacao TEXT, km INTEGER, combustivel TEXT, "
              "avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS financeiro "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, "
              "tipo_custo TEXT, valor REAL, data TEXT)")
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", 
                  (ger_hash("admin123"),))
    conn.commit()
    return conn

conn = init_db()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'u_log': "", 'p_log': ""})

if not st.session_state['auth']:
    st.title("🔑 FleetX - Login")
    with st.form("f_login"):
        u = st.text_input("ID").strip().lower()
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            res = conn.cursor().execute(
                "SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", 
                (u, ger_hash(s))
            ).fetchone()
            if res:
                st.session_state.update({'auth': True, 'u_log': u, 'p_log': res[0]})
                st.rerun()
            else: st.error("Incorreto!")
    st.stop()

st.sidebar.title("FleetX Control")
st.sidebar.markdown(f"👤 `{st.session_state['u_log']}` | 🛡️ `{st.session_state['p_log']}`")

menu = st.sidebar.radio(
    "Navegação:", 
    ["🚗 Cadastros", "📋 Visualizar & Editar", "📍 Atualizar KM", "📝 Checklist de Campo", "⛽ Abastecimento"]
)

if st.sidebar.button("🚪 Sair", type="primary", use_container_width=True):
    st.session_state['auth'] = False
    st.rerun()

try: df_glob = pd.read_sql_query("SELECT placa FROM veiculos", conn)
except: df_glob = pd.DataFrame(columns=['placa'])

if menu == "🚗 Cadastros":
    st.title("🚗 Central de Cadastros")
    tb1, tb2 = st.tabs(["Veículo", "Motorista"])
    with tb1:
        tf = st.selectbox("Modalidade", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        ln = st.text_input("Locadora") if tf == "Locadora" else None
        with st.form("f_veic", clear_on_submit=True):
            p, m = st.text_input("Placa").upper().strip(), st.text_input("Modelo")
            ki = st.number_input("KM Inicial", min_value=0)
            kr = st.number_input("Revisão KM", min_value=0)
            tr, doc = st.text_input("Trecho"), st.text_area("Obs")
            up = st.file_uploader("CRLV", type=["pdf", "png", "jpg"])
            if st.form_submit_button("Salvar Veículo") and p and m:
                try:
                    conn.cursor().execute(
                        "INSERT INTO veiculos VALUES (?,?,?, 'Disponível', ?,?,?,?,?,?, NULL, NULL)", 
                        (p, m, ki, kr, tr, tf, doc, up.read() if up else None, ln)
                    )
                    conn.commit(); st.success("Salvo!"); st.rerun()
                except: st.error("Erro ou Placa Duplicada.")
    with tb2:
        with st.form("f_mot", clear_on_submit=True):
            nome, cnh = st.text_input("Nome"), st.text_input("Nº CNH")
            venc = st.date_input("Vencimento")
            u_cnh = st.file_uploader("CNH", type=["pdf", "png", "jpg"])
            u_ter = st.file_uploader("Termo", type=["pdf", "png", "jpg"])
            if st.form_submit_button("Salvar Motorista") and nome and cnh:
                try:
                    conn.cursor().execute(
                        "INSERT INTO motoristas VALUES (?,?,?, 'Sim', ?,?)", 
                        (nome, cnh, str(venc), u_cnh.read() if u_cnh else None, u_ter.read() if u_ter else None)
                    )
                    conn.commit(); st.success("Cadastrado!"); st.rerun()
                except: st.error("Erro ao cadastrar.")

elif menu == "📋 Visualizar & Editar":
    st.title("📋 Central de Dados Dinâmica")
    st.info("💡 Edite as células e clique em Salvar.")
    t_v, t_m = st.tabs(["Frota", "Motoristas"])
    
    with t_v:
        df_v = pd.read_sql_query(
            "SELECT placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota FROM veiculos", 
            conn
        )
        edit_v = st.data_editor(df_v, num_rows="dynamic", use_container_width=True, key="ed_vc")
        if st.button("💾 Salvar Alterações da Frota"):
            conn.cursor().execute("DELETE FROM veiculos")
            for _, r in edit_v.iterrows():
                conn.cursor().execute(
                    "INSERT OR REPLACE INTO veiculos "
                    "(placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (r['placa'], r['modelo'], r['km_atual'], r['status'], r['km_proxima_revisao'], r['trecho'], r['tipo_frota'])
                )
            conn.commit(); st.success("Frota Atualizada!"); st.rerun()
            
    with t_m:
        df_m = pd.read_sql_query("SELECT nome, cnh_numero, cnh_vencimento FROM motoristas", conn)
        edit_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True, key="ed_mt")
        if st.button("💾 Salvar Alterações de Motoristas"):
            conn.cursor().execute("DELETE FROM motoristas")
            for _, r in edit_m.iterrows():
                conn.cursor().execute(
                    "INSERT OR REPLACE INTO motoristas "
                    "(nome, cnh_numero, cnh_vencimento) "
                    "VALUES (?, ?, ?)", 
                    (r['nome'], r['cnh_numero'], r['cnh_vencimento'])
                )
            conn.commit(); st.success("Motoristas Atualizados!"); st.rerun()

elif menu == "📍 Atualizar KM":
    st.title("📍 Atualizar Hodômetro")
    if not df_glob.empty:
        with st.form("f_km"):
            pl = st.selectbox("Selecione o Veículo", df_glob['placa'])
            old = int(pd.read_sql_query(f"SELECT km_atual FROM veiculos WHERE placa='{pl}'", conn)['km_atual'].values[0])
            st.metric("Hodômetro Atual", f"{old} KM")
            nv = st.number_input("Novo KM Rodado", min_value=0, step=1)
            if st.form_submit_button("Gravar Novo KM"):
                if nv <= old: st.error(f"Deve ser maior que {old} KM.")
                else:
                    conn.cursor().execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (nv, pl))
                    conn.commit(); st.success("KM atualizado!"); st.rerun()
    else: st.warning("Sem veículos.")

elif menu == "📝 Checklist de Campo":
    st.title("📝 Checklist Operacional de Campo")
    if not df_glob.empty:
        with st.form("f_chk", clear_on_submit=True):
            pl = st.selectbox("Veículo", df_glob['placa'])
            tp = st.selectbox("Movimentação", ["Entrada", "Saída", "Novo Contrato", "Devolução"])
            km = st.number_input("KM Atual", min_value=0)
            tk = st.selectbox("Combustível", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
            pn = st.radio("Pneus", ["Regular / Perfeito", "Avaria / Troca Necessária"])
            av = st.text_input("Avarias Visuais")
            if st.form_submit_button("Submeter Checklist"):
                ag = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.cursor().execute(
                    "INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                    (pl, tp, km, tk, av, pn, st.session_state['u_log'], ag)
                )
                conn.cursor().execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (km, pl))
                conn.commit(); st.success("Checklist salvo!"); st.rerun()

elif menu == "⛽ Abastecimento":
    st.title("⛽ Lançamento de Abastecimento Financeiro")
    if not df_glob.empty:
        with st.form("f_abs", clear_on_submit=True):
            pl = st.selectbox("Veículo", df_glob['placa'])
            val = st.number_input("Valor Total Pago (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Lançar Nota"):
                if val > 0:
                    conn.cursor().execute(
                        "INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", 
                        (pl, val, datetime.now().strftime("%Y-%m-%d"))
                    )
                    conn.commit(); st.success("Registrado!"); st.rerun()
