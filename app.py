import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
import altair as alt

st.set_page_config(page_title="FleetX", layout="wide")

def ger_hash(s): 
    return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    # Atualizado para v9 para acomodar os novos campos de texto e arquivos
    conn = sqlite3.connect('frotas_v9.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS usuarios "
              "(usuario TEXT PRIMARY KEY, senha_hash TEXT, perfil TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS veiculos "
              "(placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, "
              "status TEXT DEFAULT 'Disponível', km_proxima_revisao INTEGER, "
              "trecho TEXT, tipo_frota TEXT, documento TEXT, "
              "ano INTEGER, combustivel TEXT, cor TEXT, renavam TEXT, chassi TEXT, "
              "arquivo_crlv BLOB, locadora_nome TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS motoristas "
              "(nome TEXT PRIMARY KEY, cnh_numero TEXT, cnh_vencimento TEXT, "
              "termo_aceite TEXT, cpf TEXT, telefone TEXT, categoria_cnh TEXT, "
              "arquivo_cnh BLOB, arquivo_termo BLOB)")
    c.execute("CREATE TABLE IF NOT EXISTS checklists "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, "
              "tipo_movimentacao TEXT, km INTEGER, combustivel TEXT, "
              "avarias TEXT, pneus_estado TEXT, operador TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS financeiro "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, "
              "tipo_custo TEXT, valor REAL, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ordens_servico "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, tipo TEXT, "
              "descricao TEXT, custo REAL, status TEXT DEFAULT 'Pendente', "
              "data TEXT)")
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
    ["📊 Dashboard", "🚗 Cadastros", "📋 Visualizar & Editar", 
     "📍 Atualizar KM", "📝 Checklist de Campo", "⛽ Abastecimento", "🛠️ Ordens de Serviço"]
)

if st.sidebar.button("🚪 Sair", type="primary", use_container_width=True):
    st.session_state['auth'] = False
    st.rerun()

# --- MÓDULO: DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Painel Executivo de Frotas")
    st.markdown("Análise de desempenho, controle de custos e alertas operacionais em tempo real.")
    
    # 1. LINHA DE MÉTRICAS (KPIs)
    c1, c2, c3, c4 = st.columns(4)
    tot_v = conn.cursor().execute("SELECT count(*) FROM veiculos").fetchone()[0]
    tot_m = conn.cursor().execute("SELECT count(*) FROM motoristas").fetchone()[0]
    cst_tot = conn.cursor().execute("SELECT sum(valor) FROM financeiro").fetchone()[0] or 0.0
    os_pnd = conn.cursor().execute("SELECT count(*) FROM ordens_servico WHERE status='Pendente'").fetchone()[0]
    
    # Busca veículos com revisão vencida (KM Atual >= KM Próxima Revisão)
    rev_vencidas = conn.cursor().execute("SELECT count(*) FROM veiculos WHERE km_atual >= km_proxima_revisao AND km_proxima_revisao > 0").fetchone()[0]
    
    c1.metric("Frota Cadastrada", f"{tot_v} Veículos")
    c2.metric("Motoristas Ativos", f"{tot_m} Condutores")
    c3.metric("Investimento Global", f"R$ {cst_tot:,.2f}")
    c4.metric("Avisos Críticos", f"{os_pnd + rev_vencidas} Alertas", 
              delta=f"{rev_vencidas} revisões atrasadas" if rev_vencidas > 0 else "Manutenções em dia", delta_color="inverse")
    
    st.markdown("---")
    
    # 2. GRÁFICOS PRINCIPAIS (CUSTOS E STATUS)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Distribuição de Custos")
        df_cat = pd.read_sql_query("SELECT tipo_custo as Categoria, sum(valor) as Total FROM financeiro GROUP BY tipo_custo", conn)
        if not df_cat.empty:
            chart = alt.Chart(df_cat).mark_arc(innerRadius=60).encode(
                theta='Total:Q', color='Categoria:N', tooltip=['Categoria', 'Total']
            ).properties(height=280)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aguardando lançamentos financeiros para gerar o gráfico de custos.")
            
    with col2:
        st.subheader("📋 Status Operacional da Frota")
        df_st = pd.read_sql_query("SELECT status as Status, count(*) as Quantidade FROM veiculos GROUP BY status", conn)
        if not df_st.empty:
            chart_bar = alt.Chart(df_st).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('Status:N', axis=alt.Axis(labelAngle=0)), 
                y='Quantidade:Q', 
                color='Status:N',
                tooltip=['Status', 'Quantidade']
            ).properties(height=280)
            st.altair_chart(chart_bar, use_container_width=True)
        else:
            st.info("Nenhum veículo mapeado para exibir a distribuição de status.")

    st.markdown("---")
    
    # 3. NOVO INDICADOR: EVOLUÇÃO MENSAL DOS GASTOS
    st.subheader("📈 Histórico e Tendência de Despesas Mensais")
    # Consulta estruturada para agrupar despesas por Ano-Mês
    df_mes = pd.read_sql_query(
        "SELECT strftime('%Y-%m', data) as Mês, sum(valor) as Total FROM financeiro WHERE data IS NOT NULL GROUP BY Mês ORDER BY Mês ASC", conn
    )
    if not df_mes.empty and len(df_mes) > 0:
        chart_line = alt.Chart(df_mes).mark_line(point=True, color="#26b47a").encode(
            x='Mês:N',
            y='Total:Q',
            tooltip=['Mês', 'Total']
        ).properties(height=220)
        st.altair_chart(chart_line, use_container_width=True)
    else:
        st.info("Dados insuficientes para projetar a linha de tendência mensal. Continue alimentando o sistema.")

    st.markdown("---")

    # 4. NOVO INDICADOR: PAINEL DE ADVERTÊNCIAS OPERACIONAIS
    st.subheader("⚠️ Painel de Atenção e Alertas Preventivos")
    
    alertas_lista = []
    
    # Verificação 1: Revisões de KM vencidas
    veics_rev = conn.cursor().execute("SELECT placa, modelo, km_atual, km_proxima_revisao FROM veiculos WHERE km_atual >= km_proxima_revisao AND km_proxima_revisao > 0").fetchall()
    for v in veics_rev:
        alertas_lista.append({"Veículo/Origem": f"{v[0]} - {v[1]}", "Criticidade": "🔴 Alta", "Detalhe do Alerta": f"Revisão ultrapassada! KM Atual ({v[2]}) está acima do limite ({v[3]})"})
        
    # Verificação 2: Pneus com problemas no último checklist
    veics_pneu = conn.cursor().execute("SELECT placa, pneus_estado, data FROM checklists WHERE pneus_estado = 'Troca Necessária' ORDER BY id DESC").fetchall()
    # Filtra para mostrar apenas o alerta mais recente por placa
    placas_vistas = set()
    for p in veics_pneu:
        if p[0] not in placas_vistas:
            alertas_lista.append({"Veículo/Origem": p[0], "Criticidade": "🟡 Média", "Detalhe do Alerta": f"Último checklist acusou: Necessita troca de pneus ({p[2]})"})
            placas_vistas.add(p[0])
            
    # Verificação 3: Ordens de Serviço paradas
    os_abertas = conn.cursor().execute("SELECT id, placa, tipo, custo FROM ordens_servico WHERE status = 'Pendente'").fetchall()
    for o in os_abertas:
        alertas_lista.append({"Veículo/Origem": f"O.S. № {o[0]} ({o[1]})", "Criticidade": "🔵 Informativa", "Detalhe do Alerta": f"Manutenção {o[2]} aguardando aprovação. Orçamento: R$ {o[3]:,.2f}"})
        
    if alertas_lista:
        df_alertas = pd.DataFrame(alertas_lista)
        st.dataframe(df_alertas, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 Excelente! Nenhum alerta operacional ativo ou pendência detectada na frota.")
# --- MÓDULO: CADASTROS ---
elif menu == "🚗 Cadastros":
    st.title("🚗 Central de Cadastros")
    tb1, tb2 = st.tabs(["Veículo", "Motorista"])
    with tb1:
        tf = st.selectbox("Modalidade", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        ln = st.text_input("Locadora") if tf == "Locadora" else None
        with st.form("f_veic", clear_on_submit=True):
            p = st.text_input("Placa").upper().strip()
            m = st.text_input("Modelo")
            ki = st.number_input("KM Inicial", min_value=0)
            kr = st.number_input("Revisão KM", min_value=0)
            tr = st.text_input("Trecho")
            doc = st.text_area("Obs")
            if st.form_submit_button("Salvar Veículo") and p and m:
                try:
                    conn.cursor().execute(
                        "INSERT INTO veiculos (placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota, documento, locadora_nome) VALUES (?,?,?, 'Disponível', ?,?,?,?,?)", 
                        (p, m, ki, kr, tr, tf, doc, ln)
                    )
                    conn.commit(); st.success("Veículo salvo!"); st.rerun()
                except: st.error("Erro ou Placa Duplicada.")
    with tb2:
        with st.form("f_mot", clear_on_submit=True):
            nome = st.text_input("Nome")
            cnh = st.text_input("Nº CNH")
            venc = st.date_input("Vencimento")
            if st.form_submit_button("Salvar Motorista") and nome and cnh:
                try:
                    conn.cursor().execute(
                        "INSERT INTO motoristas (nome, cnh_numero, cnh_vencimento, termo_aceite) VALUES (?,?,?, 'Sim')", 
                        (nome, cnh, str(venc))
                    )
                    conn.commit(); st.success("Motorista cadastrado!"); st.rerun()
                except: st.error("Erro ao cadastrar.")

# --- MÓDULO: VISUALIZAR & EDITAR ---
elif menu == "📋 Visualizar & Editar":
    st.title("📋 Central de Dados Dinâmica")
    t_v, t_m = st.tabs(["Frota", "Motoristas"])
    with t_v:
        df_v = pd.read_sql_query("SELECT placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota FROM veiculos", conn)
        if not df_v.empty:
            edit_v = st.data_editor(df_v, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Salvar Alterações da Frota"):
                conn.cursor().execute("DELETE FROM veiculos")
                for _, r in edit_v.iterrows():
                    conn.cursor().execute(
                        "INSERT OR REPLACE INTO veiculos (placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (r['placa'], r['modelo'], r['km_atual'], r['status'], r['km_proxima_revisao'], r['trecho'], r['tipo_frota'])
                    )
                conn.commit(); st.success("Frota Atualizada!"); st.rerun()
        else: st.info("Nenhum veículo cadastrado.")
    with t_m:
        df_m = pd.read_sql_query("SELECT nome, cnh_numero, cnh_vencimento FROM motoristas", conn)
        if not df_m.empty:
            edit_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Salvar Alterações de Motoristas"):
                conn.cursor().execute("DELETE FROM motoristas")
                for _, r in edit_m.iterrows():
                    conn.cursor().execute(
                        "INSERT OR REPLACE INTO motoristas (nome, cnh_numero, cnh_vencimento) VALUES (?, ?, ?)", 
                        (r['nome'], r['cnh_numero'], r['cnh_vencimento'])
                    )
                conn.commit(); st.success("Motoristas Atualizados!"); st.rerun()
        else: st.info("Nenhum motorista cadastrado.")

# --- MÓDULO: ATUALIZAR KM ---
elif menu == "📍 Atualizar KM":
    st.title("📍 Atualizar Hodômetro")
    df_l = pd.read_sql_query("SELECT placa FROM veiculos", conn)
    if not df_l.empty:
        with st.form("f_km"):
            pl = st.selectbox("Selecione o Veículo", df_l['placa'])
            old = int(pd.read_sql_query(f"SELECT km_atual FROM veiculos WHERE placa='{pl}'", conn)['km_atual'].values[0])
            st.metric("Hodômetro Atual", f"{old} KM")
            nv = st.number_input("Novo KM Rodado", min_value=0, step=1)
            if st.form_submit_button("Gravar Novo KM"):
                if nv <= old: st.error("Deve ser maior.")
                else:
                    conn.cursor().execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (nv, pl))
                    conn.commit(); st.success("KM atualizado!"); st.rerun()
    else: st.warning("Cadastre um veículo primeiro na aba 'Cadastros'.")

# --- MÓDULO: CHECKLIST ---
elif menu == "📝 Checklist de Campo":
    st.title("📝 Checklist Operacional de Campo")
    df_l = pd.read_sql_query("SELECT placa FROM veiculos", conn)
    if not df_l.empty:
        with st.form("f_chk", clear_on_submit=True):
            pl = st.selectbox("Veículo", df_l['placa'])
            tp = st.selectbox("Movimentação", ["Entrada", "Saída"])
            km = st.number_input("KM Atual", min_value=0)
            tk = st.selectbox("Combustível", ["Reserva", "1/4", "1/2", "3/4", "Cheio"])
            pn = st.radio("Pneus", ["Regular", "Troca Necessária"])
            av = st.text_input("Avarias Visuais")
            if st.form_submit_button("Submeter Checklist"):
                ag = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.cursor().execute(
                    "INSERT INTO checklists (placa, tipo_movimentacao, km, combustivel, avarias, pneus_estado, operador, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                    (pl, tp, km, tk, av, pn, st.session_state['u_log'], ag)
                )
                conn.cursor().execute("UPDATE veiculos SET km_atual = ? WHERE placa = ?", (km, pl))
                conn.commit(); st.success("Checklist salvo!"); st.rerun()
    else: st.warning("Cadastre um veículo primeiro na aba 'Cadastros'.")

# --- MÓDULO: ABASTECIMENTO ---
elif menu == "⛽ Abastecimento":
    st.title("⛽ Lançamento de Abastecimento Financeiro")
    df_l = pd.read_sql_query("SELECT placa FROM veiculos", conn)
    if not df_l.empty:
        with st.form("f_abs", clear_on_submit=True):
            pl = st.selectbox("Veículo", df_l['placa'])
            val = st.number_input("Valor Pago (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Lançar Nota"):
                if val > 0:
                    conn.cursor().execute(
                        "INSERT INTO financeiro (placa, tipo_custo, valor, data) VALUES (?, 'Combustível', ?, ?)", 
                        (pl, val, datetime.now().strftime("%Y-%m-%d"))
                    )
                    conn.commit(); st.success("Registrado!"); st.rerun()
    else: st.warning("Cadastre um veículo primeiro na aba 'Cadastros'.")

# --- MÓDULO: ORDENS DE SERVIÇO ---
elif menu == "🛠️ Ordens de Serviço":
    st.title("🛠️ Gestão de Ordens de Serviço (O.S.)")
    t1, t2 = st.tabs(["Abrir Nova O.S.", "Histórico"])
    df_l = pd.read_sql_query("SELECT placa FROM veiculos", conn)
    with t1:
        if not df_l.empty:
            with st.form("f_os", clear_on_submit=True):
                pl = st.selectbox("Veículo", df_l['placa'])
                tp = st.selectbox("Tipo", ["Preventiva", "Corretiva"])
                cst = st.number_input("Custo (R$)", min_value=0.0, step=50.0)
                desc = st.text_area("Descrição")
                if st.form_submit_button("Emitir O.S."):
                    dt = datetime.now().strftime("%Y-%m-%d")
                    conn.cursor().execute("INSERT INTO ordens_servico (placa, tipo, descricao, custo, status, data) VALUES (?, ?, ?, ?, 'Pendente', ?)", (pl, tp, desc, cst, dt))
                    conn.commit(); st.success("O.S. registrada!"); st.rerun()
        else: st.warning("Cadastre um veículo primeiro na aba 'Cadastros'.")
    with t2:
        df_os = pd.read_sql_query("SELECT * FROM ordens_servico ORDER BY id DESC", conn)
        if not df_os.empty:
            st.dataframe(df_os, use_container_width=True)
        else: st.info("Nenhuma O.S. gerada.")
