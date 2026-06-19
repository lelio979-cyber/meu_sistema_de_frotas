import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import altair as alt

st.set_page_config(page_title="FleetX", layout="wide", initial_sidebar_state="expanded")

DB_MULTAS = {
    "7455-0": {"grav": "Média", "pts": 4, "val": 130.16, "desc": "Até 20% acima"},
    "7463-0": {"grav": "Grave", "pts": 5, "val": 195.23, "desc": "20% a 50% acima"},
    "5010-0": {"grav": "Gravíssima", "pts": 7, "val": 880.41, "desc": "Sem CNH/Vencida"}
}

def ger_hash(s): return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('frotas_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, status TEXT DEFAULT 'Disponível', km_proxima_revisao INTEGER, trecho TEXT DEFAULT 'Base', tipo_frota TEXT, documento TEXT, arquivo_crlv BLOB, locadora_nome TEXT, data_locacao TEXT, data_devolucao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS checklists (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_movimentacao TEXT, km INTEGER, combustivel TEXT, avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS ordens_servico (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, descricao TEXT, custo REAL, status TEXT DEFAULT 'Aguardando Aprovação', data TEXT, aprovado_por TEXT, data_aprovacao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo_custo TEXT, valor REAL, data TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, data TEXT, endereco TEXT, codigo TEXT, gravidade TEXT, pontos INTEGER, valor REAL, descricao TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS motoristas (nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, termo_aceite TEXT, arquivo_cnh BLOB, arquivo_termo BLOB)""")
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)""")
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('admin', ?, 'Gestor')", (ger_hash("admin123"),))
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
            res = conn.cursor().execute("SELECT perfil FROM usuarios WHERE usuario = ? AND senha_hash = ?", (u, ger_hash(s))).fetchone()
            if res:
                st.session_state.update({'auth': True, 'u_log': u, 'p_log': res[0]})
                st.rerun()
            else: st.error("Incorreto!")
    st.stop()

# --- SIDEBAR COMPACTO ---
st.sidebar.title("FleetX Control")
st.sidebar.markdown(f"👤 `{st.session_state['u_log']}` | 🛡️ `{st.session_state['p_log']}`")

def check_cnh_sidebar():
    try:
        for n, v in conn.cursor().execute("SELECT nome, cnh_vencimento FROM motoristas").fetchall():
            dias = (datetime.strptime(v, "%Y-%m-%d").date() - date.today()).days
            if dias < 0: st.sidebar.error(f"🚨 VENCIDA: {n}")
            elif dias <= 30: st.sidebar.warning(f"⚠️ {dias}d: {n}")
    except: pass

check_cnh_sidebar()

menus = ["📊 Dashboard", "📋 Auditoria", "🚗 Cadastros", "👥 Usuários", "📍 Atualizar KM", "📋 Checklist", "⛽ Abastecer", "🛠️ O.S.", "⚠️ Multas", "📝 Contratos"] if st.session_state['p_log'] == 'Gestor' else ["📍 Atualizar KM", "📋 Checklist", "⛽ Abastecer", "📋 Auditoria"]
esc = st.sidebar.radio("Navegação:", menus)

if st.sidebar.button("🚪 Sair", type="primary", use_container_width=True):
    st.session_state['auth'] = False
    st.rerun()

try: df_glob = pd.read_sql_query("SELECT placa FROM veiculos", conn)
except: df_glob = pd.DataFrame(columns=['placa'])

# --- FUNÇÕES DE RENDERIZAÇÃO ---
def render_dashboard():
    st.title("📊 Painel Executivo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Frota", f"{conn.cursor().execute('SELECT count(*) FROM veiculos').fetchone()[0]} veic.")
    c2.metric("Condutores", f"{conn.cursor().execute('SELECT count(*) FROM motoristas').fetchone()[0]} mot.")
    c3.metric("Despesa Global", f"R$ {conn.cursor().execute('SELECT sum(valor) FROM financeiro').fetchone()[0] or 0.0:,.2f}")
    os_p = conn.cursor().execute("SELECT count(*) FROM ordens_servico WHERE status='Aguardando Aprovação'").fetchone()[0]
    c4.metric("O.S. Pendentes", f"{os_p} apr.", delta=f"{os_p} urgentes" if os_p > 0 else "Em dia")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Custos por Categoria")
        df_cat = pd.read_sql_query("SELECT tipo_custo, sum(valor) as total FROM financeiro GROUP BY tipo_custo", conn)
        if not df_cat.empty:
            st.altair_chart(alt.Chart(df_cat).mark_arc(innerRadius=50).encode(theta='total:Q', color='tipo_custo:N'), use_container_width=True)
    with col2:
        st.subheader("🚗 Status da Frota")
        df_status = pd.read_sql_query("SELECT status, count(*) as total FROM veiculos GROUP BY status", conn)
        if not df_status.empty:
            st.altair_chart(alt.Chart(df_status).mark_bar().encode(x='status:N', y='total:Q', color='status:N'), use_container_width=True)
            
    st.markdown("---")
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("🚨 Últimas Multas")
        df_m = pd.read_sql_query("SELECT placa, data, gravidade, valor FROM multas ORDER BY data DESC LIMIT 4", conn)
        st.dataframe(df_m, use_container_width=True, hide_index=True) if not df_m.empty else st.success("Sem multas.")
    with g2:
        st.subheader("💡 Ranking: Custos por Veículo")
        df_top = pd.read_sql_query("SELECT placa, sum(valor) as total_gasto FROM financeiro GROUP BY placa ORDER BY total_gasto DESC LIMIT 4", conn)
        st.dataframe(df_top, use_container_width=True, hide_index=True) if not df_top.empty else st.info("Sem despesas.")

def render_auditoria():
    st.title("📋 Central de Auditoria")
    t1, t2, t3, t4, t5 = st.tabs(["Checklists", "Financeiro", "OS", "Frota", "Motoristas"])
    with t1: st.dataframe(pd.read_sql_query("SELECT * FROM checklists ORDER BY data DESC", conn), use_container_width=True)
    with t2: st.dataframe(pd.read_sql_query("SELECT * FROM financeiro ORDER BY data DESC", conn), use_container_width=True)
    with t3: st.dataframe(pd.read_sql_query("SELECT * FROM ordens_servico ORDER BY id DESC", conn), use_container_width=True)
    with t4: st.dataframe(pd.read_sql_query("SELECT * FROM veiculos", conn), use_container_width=True)
    with t5: st.dataframe(pd.read_sql_query("SELECT * FROM motoristas", conn), use_container_width=True)

def render_cadastros():
    st.title("🚗 Central de Cadastros")
    tb1, tb2, tb3 = st.tabs(["Veículo", "Motorista", "📥 Arquivos"])
    with tb1:
        tf = st.selectbox("Modalidade", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        ln, ld = (st.text_input("Locadora"), str(st.date_input("Vigência"))) if tf == "Locadora" else (None, None)
        with st.form("f_veic", clear_on_submit=True):
            p, m = st.text_input("Placa").upper().strip(), st.text_input("Modelo")
            ki, kr = st.number_input("KM Inicial", min_value=0), st.number_input("Revisão KM", min_value=0)
            tr, doc = st.text_input("Trecho"), st.text_area("Obs")
            up = st.file_uploader("CRLV", type=["pdf", "png", "jpg"])
            if st.form_submit_button("Salvar") and p and m:
                try:
                    conn.cursor().execute("INSERT INTO veiculos VALUES (?,?,?, 'Disponível', ?,?,?,?,?,?,?, NULL)", (p, m, ki, kr, tr, tf, doc, up.read() if up else None, ln, ld))
                    conn.commit(); st.success("Salvo!"); st.rerun()
                except: st.error("Erro ou Duplicado.")
    with tb2:
        with st.form("f_mot", clear_on_submit=True):
            nome, cnh = st.text_input("Nome"), st.text_input("Nº CNH")
            venc = st.date_input("Vencimento")
            u_cnh = st.file_uploader("CNH", type=["pdf", "png", "jpg"])
            u_ter = st.file_uploader("Termo", type=["pdf", "png", "jpg"])
            if st.form_submit_button("Salvar") and nome and cnh:
                conn.cursor().execute("INSERT INTO motoristas VALUES (?,?,?, 'Sim', ?,?)", (nome, cnh, str(venc), u_cnh.read() if u_cnh else None, u_ter.read() if u_ter else None))
                conn.commit(); st.success("Cadastrado!"); st.rerun()
    with tb3:
        for pl, b in conn.cursor().execute("SELECT placa, arquivo_crlv FROM veiculos WHERE arquivo_crlv IS NOT NULL").fetchall():
            st.download_button(f"📥 CRLV - {pl}", data=b, file_name=f"CRLV_{pl}.pdf")

def render_usuarios():
    st.title("👥 Acessos")
    with st.form("f_user", clear_on_submit=True):
        u, s = st.text_input("Login").strip().lower(), st.text_input("Senha", type="password")
        p = st.selectbox("Perfil", ["Operador", "Gestor"])
        if st.form_submit_button("Criar") and u and s:
            try:
                conn.cursor().execute("INSERT INTO usuarios VALUES (?, ?, ?)", (u, ger_hash(s), p))
                conn.commit(); st.success("Criado!")
            except: st.error("Indisponível.")

def render_km():
    st.title("📍 Atualizar Hodômetro")
    df = pd.read_sql_query("SELECT placa, km_atual FROM veiculos", conn)
    if not df.empty:
        with st.form("f_km"):
            pl = st.selectbox("Veículo", df['placa'])
            old = int(df[df['placa'] == pl]['km_atual'].values[0])
            st.info(f"KM Actual: {old} KM")
            nv = st.number_input("Novo KM", min_value=0)
            if st.form_submit_button("Atualizar"):
                if nv <= old: st.error("Deve ser maior!")
                else:
                    conn.cursor().execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (nv, pl))
                    conn.commit(); st.success("Atualizado!"); st.rerun()

def render_checklist():
    st.title("📋 Checklist")
    if not df_glob.empty:
        with st.form("f_chk", clear_on_submit=True):
            pl = st.selectbox("Placa", df_glob['placa'])
            tp = st.selectbox("Natureza", ["Entrada", "Saída", "Novo Contrato", "Devolução"])
            km = st.number_input("KM", min_value=0)
            tk = st.selectbox("Tanque", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
            pn = st.radio("Pneus", ["Regular", "Avaria"])
            av = st.text_input("Avarias")
            if st.form_submit_button("Submeter"):
                ag, hj = datetime.now().strftime("%Y-%m-%d %H:%M"), datetime.now().strftime("%Y-%m-%d")
                conn.cursor().execute("INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) VALUES (?,?,?,?,?,?,?,?)", (pl, tp, km, tk, av, pn, st.session_state['u_log'], ag))
                if tp == "Devolução":
                    d = conn.cursor().execute("SELECT data_locacao, tipo_frota FROM veiculos WHERE placa = ?", (pl,)).fetchone()
                    conn.cursor().execute("UPDATE veiculos SET status = 'Disponível', data_devolucao = ? WHERE placa = ?", (hj, pl))
                    if d and d[1] == "Locadora" and d[0]: st.info(f"Uso: {abs((datetime.strptime(hj, '%Y-%m-%d') - datetime.strptime(d[0], '%Y-%m-%d')).days)} dias.")
                conn.commit(); st.success("Salvo!"); st.rerun()

def render_abastecimento():
    st.title("⛽ Abastecimento")
    if not df_glob.empty:
        with st.form("f_abs"):
            pl = st.selectbox("Placa", df_glob['placa'])
            val = st.number_input("Valor (R$)", min_value=0.0)
            if st.form_submit_button("Lançar") and val > 0:
                conn.cursor().execute("INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", (pl, val, datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.success("Lançado!"); st.rerun()

def render_os():
    st.title("🛠️ Ordens de Serviço")
    if not df_glob.empty:
        ta, tf = st.tabs(["Abrir OS", "Pendentes"])
        with ta:
            with st.form("f_os"):
                pl = st.selectbox("Placa", df_glob['placa'])
                tp = st.selectbox("Tipo", ["Preventiva", "Corretiva"])
                desc, cst = st.text_area("Escopo"), st.number_input("Custo (R$)", min_value=0.0)
                if st.form_submit_button("Gerar OS"):
                    conn.cursor().execute("INSERT INTO ordens_servico (placa, tipo, descricao, custo, status, data, aprovado_por, data_aprovacao) VALUES (?,?,?,?,'Aguardando Aprovação',?, NULL, NULL)", (pl, tp, desc, cst, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st
