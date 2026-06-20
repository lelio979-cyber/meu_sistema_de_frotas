import streamlit as st
import banco  # Importa o arquivo banco.py que criamos antes

# Configuração da página
st.set_page_config(page_title="SGF-Pro Login", layout="centered")

def tela_login():
    st.title("🔐 Acesso Restrito")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Consulta no banco de dados para verificar credenciais e perfil
        conn = banco.get_connection()
        user = conn.execute("SELECT perfil FROM usuarios WHERE login=? AND senha=?", (usuario, senha)).fetchone()
        conn.close()
        
        if user:
            st.session_state['logado'] = True
            st.session_state['perfil'] = user[0] # Armazena 'admin' ou 'operador'
            st.rerun()
        else:
            st.error("Credenciais inválidas!")

def main():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False

    if not st.session_state['logado']:
        tela_login()
    else:
        # MENU RESTRITO POR PERFIL
        perfil = st.session_state['perfil']
        
        st.sidebar.title(f"Olá, {perfil.capitalize()}")
        menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro"])
        
        if menu == "Cadastro":
            if perfil == "admin":
                st.write("Bem-vindo ao formulário de cadastro (Apenas Admins).")
                # Aqui você colocaria o código de cadastro
            else:
                st.error("Você não tem permissão para acessar esta área.")
