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
     "📍 Atualizar KM", "📝 Checklist de Campo", "⛽ Abastecimento", "🛠️ Ordens de Serviço", "📋 Auditoria de Checklists"]
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
    st.title("🚗 Central de Cadastros Avançada")
    st.markdown("Insira os dados patrimoniais e operacionais da frota com upload de documentos obrigatórios.")
    
    tb1, tb2 = st.tabs(["📋 Cadastro de Veículo", "👤 Cadastro de Motorista"])
    
    with tb1:
        st.subheader("Dados do Veículo")
        tf = st.selectbox("Modalidade da Frota", ["Próprio", "Reserva", "Terceirizado", "Locadora"])
        ln = st.text_input("Nome da Locadora") if tf == "Locadora" else None
        
        with st.form("f_veic", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                p = st.text_input("Placa (Ex: ABC1D23 / ABC1234)").upper().strip().replace("-", "")
                m = st.text_input("Modelo / Marca")
                ano = st.number_input("Ano Fabricação/Modelo", min_value=1980, max_value=2030, value=2025)
            with col2:
                ki = st.number_input("Odômetro Inicial (KM)", min_value=0, step=1)
                kr = st.number_input("Próxima Revisão (KM)", min_value=0, step=1)
                cor = st.text_input("Cor Predominante")
            with col3:
                comb = st.selectbox("Combustível Padrão", ["Flex", "Gasolina", "Etanol", "Diesel", "Elétrico"])
                tr = st.text_input("Trecho / Operação Atribuída")
                
            col_doc1, col_doc2 = st.columns(2)
            with col_doc1:
                renavam = st.text_input("Número do RENAVAM")
            with col_doc2:
                chassi = st.text_input("Número do Chassi")
                
            doc = st.text_area("Observações Gerais Básicas")
            up_crlv = st.file_uploader("Anexar Documento CRLV (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
            
            if st.form_submit_button("💾 Salvar Veículo na Frota"):
                if not p or len(p) < 7:
                    st.error("❌ Digite uma placa válida com pelo menos 7 caracteres.")
                elif not m:
                    st.error("❌ O modelo do veículo é obrigatório.")
                else:
                    try:
                        crlv_bytes = up_crlv.read() if up_crlv else None
                        conn.cursor().execute(
                            "INSERT INTO veiculos (placa, modelo, km_atual, status, km_proxima_revisao, trecho, tipo_frota, documento, ano, combustivel, cor, renavam, chassi, arquivo_crlv, locadora_nome) "
                            "VALUES (?,?,?, 'Disponível', ?,?,?,?,?,?,?,?,?,?,?)", 
                            (p, m, ki, kr, tr, tf, doc, ano, comb, cor, renavam, chassi, crlv_bytes, ln)
                        )
                        conn.commit()
                        st.success(f"🚗 Veículo de Placa {p} cadastrado com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Erro: Já existe um veículo cadastrado com esta mesma placa.")
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar no banco de dados: {e}")

    with tb2:
        st.subheader("Dados do Motorista / Condutor")
        with st.form("f_mot", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                nome = st.text_input("Nome Completo")
                cpf = st.text_input("CPF (Apenas números)")
                tel = st.text_input("Telefone de Contato (Com DDD)")
            with col_m2:
                cnh = st.text_input("Número de Registro CNH")
                cat_cnh = st.selectbox("Categoria da CNH", ["B", "A", "AB", "C", "D", "E"])
                venc = st.date_input("Data de Vencimento da CNH")
            
            st.markdown("---")
            st.markdown("##### 📁 Arquivos e Termos de Responsabilidade")
            up_cnh = st.file_uploader("Anexar CNH Digitalizada (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
            up_termo = st.file_uploader("Anexar Termo de Uso de Veículo Assinado (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
            
            if st.form_submit_button("💾 Salvar Cadastro de Motorista"):
                hoje = datetime.now().date()
                if not nome:
                    st.error("❌ O nome completo é obrigatório.")
                elif not cnh:
                    st.error("❌ O número da CNH é obrigatório.")
                elif venc < hoje:
                    st.error(f"❌ Bloqueado! A CNH informada está vencida desde {venc.strftime('%d/%m/%Y')}.")
                else:
                    try:
                        cnh_bytes = up_cnh.read() if up_cnh else None
                        termo_bytes = up_termo.read() if up_termo else None
                        conn.cursor().execute(
                            "INSERT INTO motoristas (nome, cnh_numero, cnh_vencimento, termo_aceite, cpf, telefone, categoria_cnh, arquivo_cnh, arquivo_termo) "
                            "VALUES (?,?,?, 'Sim', ?,?,?,?,?)", 
                            (nome, cnh, str(venc), cpf, tel, cat_cnh, cnh_bytes, termo_bytes)
                        )
                        conn.commit()
                        st.success(f"👤 Motorista {nome} registrado com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Erro: Já existe um motorista cadastrado com este mesmo nome ou CNH.")
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar condutor: {e}")
# --- MÓDULO: VISUALIZAR & EDITAR ---
elif menu == "📋 Visualizar & Editar":
    st.title("📋 Central de Dados Dinâmica")
    st.markdown("Visualize, edite as informações em tempo real ou baixe os documentos anexados.")
    
    t_v, t_m = st.tabs(["🚗 Frota Cadastrada", "👤 Motoristas Cadastrados"])
    
    with t_v:
        df_v = pd.read_sql_query(
            "SELECT placa, modelo, ano, cor, combustivel, km_atual, km_proxima_revisao, status, trecho, tipo_frota, renavam, chassi, documento, locadora_nome FROM veiculos", conn
        )
        if not df_v.empty:
            st.markdown("##### 📝 Tabela de Veículos (Dê um duplo clique na célula para editar)")
            edit_v = st.data_editor(df_v, num_rows="dynamic", use_container_width=True)
            
            if st.button("💾 Salvar Alterações da Frota", type="primary"):
                try:
                    # Atualiza os dados mantendo os arquivos blob intocados
                    for _, r in edit_v.iterrows():
                        conn.cursor().execute(
                            "INSERT OR REPLACE INTO veiculos (placa, modelo, ano, cor, combustivel, km_atual, km_proxima_revisao, status, trecho, tipo_frota, renavam, chassi, documento, locadora_nome, arquivo_crlv) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, (SELECT arquivo_crlv FROM veiculos WHERE placa = ?))",
                            (r['placa'], r['modelo'], r['ano'], r['cor'], r['combustivel'], r['km_atual'], r['km_proxima_revisao'], r['status'], r['trecho'], r['tipo_frota'], r['renavam'], r['chassi'], r['documento'], r['locadora_nome'], r['placa'])
                        )
                    # Remove veículos que foram deletados no editor
                    placas_ativas = tuple(edit_v['placa'].tolist())
                    if len(placas_ativas) == 1:
                        conn.cursor().execute(f"DELETE FROM veiculos WHERE placa != '{placas_ativas[0]}'")
                    elif len(placas_ativas) > 1:
                        conn.cursor().execute(f"DELETE FROM veiculos WHERE placa NOT IN {placas_ativas}")
                    
                    conn.commit()
                    st.success("✅ Banco de dados da frota sincronizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar alterações: {e}")
            
            st.markdown("---")
            st.markdown("##### 📥 Download de Documentos (CRLV)")
            placa_doc = st.selectbox("Escolha o veículo para baixar o CRLV", df_v['placa'])
            res_crlv = conn.cursor().execute("SELECT arquivo_crlv FROM veiculos WHERE placa = ?", (placa_doc,)).fetchone()
            if res_crlv and res_crlv[0]:
                st.download_button(label="📄 Baixar CRLV Anexado", data=res_crlv[0], file_name=f"CRLV_{placa_doc}.pdf", mime="application/octet-stream")
            else:
                st.info("Este veículo não possui arquivo de CRLV digitalizado.")
        else:
            st.info("Nenhum veículo cadastrado na base de dados.")
            
    with t_m:
        df_m = pd.read_sql_query("SELECT nome, cpf, telefone, cnh_numero, categoria_cnh, cnh_vencimento, termo_aceite FROM motoristas", conn)
        if not df_m.empty:
            st.markdown("##### 📝 Tabela de Motoristas (Dê um duplo clique na célula para editar)")
            edit_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True)
            
            if st.button("💾 Salvar Alterações de Motoristas", type="primary"):
                try:
                    for _, r in edit_m.iterrows():
                        conn.cursor().execute(
                            "INSERT OR REPLACE INTO motoristas (nome, cpf, telefone, cnh_numero, categoria_cnh, cnh_vencimento, termo_aceite, arquivo_cnh, arquivo_termo) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT arquivo_cnh FROM motoristas WHERE nome = ?), (SELECT arquivo_termo FROM motoristas WHERE nome = ?))",
                            (r['nome'], r['cpf'], r['telefone'], r['cnh_numero'], r['categoria_cnh'], r['cnh_vencimento'], r['termo_aceite'], r['nome'], r['nome'])
                        )
                    # Remove motoristas que foram deletados no editor
                    nomes_ativos = tuple(edit_m['nome'].tolist())
                    if len(nomes_ativos) == 1:
                        conn.cursor().execute(f"DELETE FROM motoristas WHERE nome != '{nomes_ativos[0]}'")
                    elif len(nomes_ativos) > 1:
                        conn.cursor().execute(f"DELETE FROM motoristas WHERE nome NOT IN {nomes_ativos}")
                        
                    conn.commit()
                    st.success("✅ Banco de dados de motoristas sincronizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar alterações: {e}")
                    
            st.markdown("---")
            st.markdown("##### 📥 Download de Documentos (CNH e Termos)")
            mot_doc = st.selectbox("Escolha o motorista para baixar os arquivos", df_m['nome'])
            res_mot = conn.cursor().execute("SELECT arquivo_cnh, arquivo_termo FROM motoristas WHERE nome = ?", (mot_doc,)).fetchone()
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if res_mot and res_mot[0]:
                    st.download_button(label="🪪 Baixar CNH Digitalizada", data=res_mot[0], file_name=f"CNH_{mot_doc}.pdf", mime="application/octet-stream")
                else:
                    st.info("Sem CNH anexada para este condutor.")
            with col_d2:
                if res_mot and res_mot[1]:
                    st.download_button(label="📝 Baixar Termo de Uso", data=res_mot[1], file_name=f"Termo_{mot_doc}.pdf", mime="application/octet-stream")
                else:
                    st.info("Sem Termo de Uso anexado para este condutor.")
        else:
            st.info("Nenhum motorista cadastrado na base de dados.")
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
